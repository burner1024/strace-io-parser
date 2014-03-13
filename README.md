Analyze strace output to get detailed information on i/o activity: write operations count and volume.


Sample usage:

```
strace -f -p PID_OF_PROCESS -T -tt -o strace.log
(Ctrl-C)

./strace-io-parser.py strace.log

Total strace time: 587.045493 seconds
Total write volume: 16.5615 Mb
Total write ops: 97908
Average write per op: 177 bytes
Average ops per minute: 10006.86
Average write volume per minute: 1733.32Kb
Top 3 ops count:
1) unknown 3182 (3.25%)
2) /var/log/httpd/error.log 53 (0.05%)
2) /var/log/httpd/access.log 42 (0.04%)
Top 3 write volume:
1) unknown 4984.283Kb (29.39%)
2) /var/log/httpd/error.log 581.305Kb (3.43%)
3) /var/log/httpd/access.log 535.281Kb (3.16%)
```

Adjust variables in the script to change top's length.

It's recommended to leave strace running for at least a few minutes to reduce "unknown" %'s and get representative results.
