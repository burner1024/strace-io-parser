#!/usr/bin/env python

import sys
import os
import re
import datetime

from collections import defaultdict

DEBUG = False
# DEBUG = True
LOG = "strace.log"

TOP_NUMBER_OPERATIONS = 5
TOP_NUMBER_VOLUME = 5

OPEN_REGEX = re.compile('open\("(?P<filepath>[^"]+)", [^\)]*\) = (?P<descriptor>[0-9]+)')
WRITE_REGEX = re.compile('write\((?P<descriptor>[0-9]+), "[^"]+"(\.)*, (?P<amount>[0-9]+)\)')
CLOSE_REGEX = re.compile('close\((?P<descriptor>[0-9]+)\)[\s]+=')
TIME_REGEX = re.compile("([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)")
PID_REGEX = re.compile("^(?P<pid>[0-9]+)")
DUP_REGEX = re.compile(
        "dup[23]?\((?P<old_descriptor>[0-9]+), [0-9]+\)[\s]+=(?P<descriptor>[0-9]+)")


def parse_time(line):
    time_data = TIME_REGEX.search(line)
    return datetime.time(*map(int, time_data.groups()))


def log(msg):
    if not DEBUG:
        return
    print msg

def main(logfile=LOG):
    start_time = None
    operations = defaultdict(list)
    descriptors = defaultdict(dict)
    writes = []
    if not os.path.exists(logfile):
        print "Error: file %s does not exist" % logfile
        sys.exit(1)
    with open(logfile) as fp:
        prev_line = None
        for line in fp:
            prev_line = line
            if start_time is None:
                line_time = parse_time(line)
                start_time = line_time

            pid_search = PID_REGEX.search(line)
            open_search = OPEN_REGEX.search(line)
            write_search = WRITE_REGEX.search(line)
            close_search = CLOSE_REGEX.search(line)
            # some childs can duplicate fd
            # dup_search = DUP_REGEX.search(line)
            if not (write_search or open_search or close_search):
                continue
            pid_data = pid_search.groupdict()
            pid = pid_data['pid']
            if open_search:
                open_data = open_search.groupdict()
                descriptor = int(open_data['descriptor'])
                log("Set descriptor %d" % descriptor)
                descriptors[pid][descriptor] = open_data['filepath']
            elif write_search:
                search_data = write_search.groupdict()
                descriptor = int(search_data['descriptor'])
                amount = int(search_data['amount'])
                try:
                    operations[descriptors[pid][descriptor]].append(amount)
                except KeyError:
                    log('Unknown data\n%s' % line)
                    operations['unknown'].append(amount)
            elif close_search:
                close_data = close_search.groupdict()
                descriptor = int(close_data['descriptor'])
                log("Delete descriptor %d" % descriptor)
                try:
                    del descriptors[pid][descriptor]
                except KeyError:
                    log("Cannot unset descriptor %d" % descriptor)
                    log(line)
                    pass
            # elif dup_search:
            #     dup_data = dup_search.groupdict()
            #     old_descriptor = int(dup_data['old_descriptor'])
            #     new_descriptor = int(dup_data['new_descriptor'])
        last_line = prev_line
        end_time = parse_time(last_line)
    now = datetime.datetime.now()
    start_datetime = now.replace(
            hour=start_time.hour,
            minute=start_time.minute,
            second=start_time.second,
            microsecond=start_time.microsecond
            )
    end_datetime = now.replace(
            hour=end_time.hour,
            minute=end_time.minute,
            second=end_time.second,
            microsecond=end_time.microsecond
            )
    work_time = end_datetime - start_datetime
    all_writes = [i for operation in operations.values() for i in operation]
    total_bytes = sum(all_writes)
    write_num = len(all_writes)
    top5_write_num = sorted(operations, key=lambda fn: len(operations[fn]),
            reverse=True)
    top5_write_volume = sorted(operations, key=lambda fn: sum(operations[fn]),
            reverse=True)
    work_time_seconds = (24 * 60 * 60 * work_time.days +
            work_time.seconds + work_time.microseconds * 10 ** -6)

    print "Total strace time: %s seconds" % work_time_seconds
    print "Total write volume: %.4f Mb" % (total_bytes / (1024 * 1024.0), )
    print "Total write ops: %d" % write_num
    print "Average write per op: %d bytes" % (total_bytes / write_num,)
    print "Average ops per minute: %.2f" % (
            write_num / (work_time_seconds / 60),)
    print "Average write volume per minute: %.2fKb" % (
            total_bytes / (1024.0 * work_time_seconds / 60),
            )

    print "Top %d ops count:\n%s" % (TOP_NUMBER_OPERATIONS,
            '\n'.join(
            [
                '%d) %s %s (%.2f%%)' % (
                    i+1, fn, len(operations[fn]),
                    len(operations[fn]) * 100.0 / write_num)
                for i, fn in enumerate(top5_write_num[:TOP_NUMBER_OPERATIONS])
                ]
            )
            )
    print "Top %d write volume:\n%s" % (
            TOP_NUMBER_VOLUME,
            '\n'.join(
                [
                    '%d) %s %.3fKb (%.2f%%)' % (i+1, fn, sum(operations[fn])/1024.0, sum(operations[fn]) * 100.0 / total_bytes)
                    for i, fn in enumerate(top5_write_volume[:TOP_NUMBER_VOLUME])
                    ]
                )
                )
    return operations


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'No file given'
        sys.exit(1)
    fp = sys.argv[1]
    main(fp)
