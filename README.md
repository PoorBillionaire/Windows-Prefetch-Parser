# Windows-Prefetch-Parser
Parse Windows Prefetch files: Supports XP - Windows 10 Prefetch files

###Description
The Windows Prefetch file was put in place to offer performance benefits when launching applications. It just so happens to be one of the more beneficial forensic artifacts regarding evidence of applicaiton execution as well. prefetch.py provides functionality for parsing prefetch files for Windows XP, Vista, 7, 8, 8.1, and 10. An individual prefetch file can be specified, or a directory of prefetch files.

####Command-Line Options
For now, prefetch.py requires one of two command-line options: --file specifies a single prefetch to point the script at. --directory specifies an entire directory of prefetch files which will be parsed and printed to stdout:

```
dev@computer:~/$ python prefetch.py -h
usage: prefetch.py [-h] [-f FILE] [-d DIRECTORY]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Parse a given Prefetch file
  -d DIRECTORY, --directory DIRECTORY
                        Parse a directory of Prefetch files
```

####--file

Using the --file / -f switch provides the output below:

```
dev@computer:~$ python prefetch.py -f PING.EXE-7E94E73E.pf

====================
Filename: PING.EXE
====================

Run count: 13
Last executed: 2015-10-22 16:04:10.275140
Volume path: \DEVICE\HARDDISKVOLUME2
Volume serial number ee186f39

1:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\NTDLL.DLL
2:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\KERNEL32.DLL
3:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\APISETSCHEMA.DLL
4:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\KERNELBASE.DLL
5:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\LOCALE.NLS
6:  \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\PING.EXE

...
...
...
```

####--directory
By invoking the --directory / -d flag, the Analyst is able to parse an entire directory of Prefetch files at once.

###Python Requirements

* from argparse import ArgumentParser
* import binascii
* import collections
* import ctypes
* from datetime import datetime,timedelta
* import json
* import os
* import struct
* import sys
