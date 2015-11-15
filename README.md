# Windows-Prefetch-Parser
Python script created to parse Windows Prefetch files: Supports XP - Windows 10 Prefetch files

###Description
The Windows Prefetch file was put in place to offer performance benefits when launching applications. It just so happens to be one of the more beneficial forensic artifacts regarding evidence of applicaiton execution as well. prefetch.py provides functionality for parsing prefetch files for all current prefetch file versions: 17, 23, 26, and 30.

This project would not have been possible without the work of others much smarter than I. The prefetch file format is not officially documented by Microsoft and has been understood by reverse engineering, and trial-and-error. To gain a better understanding of the prefetch file format please see these resources; which were all used as references for the creation of this script:

[ForensicsWiki: Windows Prefetch File Format](http://www.forensicswiki.org/wiki/Windows_Prefetch_File_Format)

[Libyal Project: libscca ](https://github.com/libyal/libscca/blob/master/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc)

[Zena Forensics: A first look at Windows 10 Prefetch files](http://blog.digital-forensics.it/2015/06/a-first-look-at-windows-10-prefetch.html)

###Features

* Specify a single prefetch file or a directory of prefetch files
* Automatic version detection - no specification required by the user
* On-the-fly type 30 (Windows 10) decompression and parsing

####Command-Line Options
For now, prefetch.py requires one of two command-line options: --file specifies a single prefetch to point the script at. --directory specifies an entire directory of prefetch files which will be parsed and printed to stdout. When using --directory / -d, remember to include the trailing slash:

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


###Testing

Testing on the prefetch file types below has been completed successfully:

- [x] Windows XP (version 17)
- [x] Windows 7 (version 23)
- [x] Windows 8.1 (version 26)
- [x] Windows 10 (version 30)


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
