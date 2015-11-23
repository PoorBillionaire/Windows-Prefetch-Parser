#Windows-Prefetch-Parser
Python script created to parse Windows Prefetch files: Supports XP - Windows 10 Prefetch files

###Description
The Windows Prefetch file was put in place to offer performance benefits when launching applications. It just so happens to be one of the more beneficial forensic artifacts regarding evidence of applicaiton execution as well. prefetch.py provides functionality for parsing prefetch files for all current prefetch file versions: 17, 23, 26, and 30.

###Features

* Specify a single prefetch file or a directory of prefetch files
* Automatic version detection - no specification required by the user
* On-the-fly type 30 (Windows 10) decompression and parsing
* Sort a directory of Prefetch files by last execution time
* (Mostly) cross-platform: Windows 10 prefetch files must be parsed from a Windows workstation using this script. All others have been tested on both Windows and Linux

###Note: Version 30 (Windows 10)
The class being utilized for Windows 10 prefetch file decompression makes use of Python's 'ctypes' module. This module relies on the Windows API; the Analyst must be working from a workstation running at least Windows 8 in order to decompress and parse Windows 10 prefetch files.

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
  -e EXECUTED, --executed EXECUTED
                        Sort a directory of Prefetch files by last execution time
  -z ZERO, --zero ZERO  Identify empty prefetch files
```

####--file

Using the --file / -f switch provides the output below:

```
dev@computer:~$ python prefetch.py -f PING.EXE-7E94E73E.pf

===================
Filename: CMD.EXE
===================

Run count: 17
Last executed: 2015-11-14 23:32:03.051396
Additional execution timestamp(s):
    2015-11-14 23:27:20.815510
    2015-11-14 21:50:33.595482
    2015-11-14 03:22:22.545884
    2015-11-12 07:31:13.017108
    2015-11-12 06:28:31.903824
    2015-11-12 06:09:16.828206
    2015-11-12 04:26:48.679006

Volume path: \VOLUME{01d11b57aa4f5b10-e8aabf9f}
Volume serial number e8aabf9f

Resources loaded:

1:    \VOLUME{01d11b57aa4f5b10-e8aabf9f}\WINDOWS\SYSTEM32\NTDLL.DLL
2:    \VOLUME{01d11b57aa4f5b10-e8aabf9f}\WINDOWS\SYSTEM32\CMD.EXE
3:    \VOLUME{01d11b57aa4f5b10-e8aabf9f}\WINDOWS\SYSTEM32\KERNEL32.DLL
4:    \VOLUME{01d11b57aa4f5b10-e8aabf9f}\WINDOWS\SYSTEM32\KERNELBASE.DLL
5:    \VOLUME{01d11b57aa4f5b10-e8aabf9f}\WINDOWS\SYSTEM32\LOCALE.NLS
...
...
...
```

####--directory

By invoking the --directory / -d flag, the Analyst is able to parse an entire directory of Prefetch files at once.

####--executed

Sort a directory of Prefetch files by last execution time. The output looks like this:

```
dev@computer:~$ python prefetch.py -e Prefetch/

2015-10-22 18:11:34.918518 - CONHOST.EXE
2015-10-22 18:11:34.555482 - MCSCRIPT_INUSE.EXE
2015-10-22 18:10:52.214248 - ENTVUTIL.EXE
2015-10-22 18:10:15.439572 - SEARCHFILTERHOST.EXE
2015-10-22 18:10:15.285556 - SEARCHPROTOCOLHOST.EXE
...
...
...
```

####--zero

Recently I encountered multiple zero-byte Prefetch files during an investigation. This broke some of the functionality in my script, which was expecting data instead of null values. I modified the script not to break when it encounters empty Prefetch files. Additionally, I added the -z/--zero flag which will help an Analyst identify them up front:

```
dev@computer:~$ python prefetch.py -z Prefetch/

==========================
Zero-byte Prefetch Files
==========================

WERMGR.EXE-0F2AC88C.pf
WMIPRVSE.EXE-1628051C.pf

```

###Testing

Testing on the prefetch file types below has been completed successfully:

- [x] Windows XP (version 17)
- [x] Windows 7 (version 23)
- [x] Windows 8.1 (version 26)
- [x] Windows 10 (version 30)

###References
This project would not have been possible without the work of others much smarter than I. The prefetch file format is not officially documented by Microsoft and has been understood through reverse engineering, and trial-and-error. 

Additionally, Without the excellent work by Francesco Picasso in understanding the Windows 10 prefetch compression method, I would not have been able to get Windows 10 parsed here. I use a modified version of his decompression script in prefetch.py. Francesco's original script can be found at the link below:

[w10pfdecomp.py](https://github.com/dfirfpi/hotoloti/blob/master/sas/w10pfdecomp.py)

To gain a better understanding of the prefetch file format, check out the following resources; which were all used as references for the creation of my script:

[ForensicsWiki: Windows Prefetch File Format](http://www.forensicswiki.org/wiki/Windows_Prefetch_File_Format)

[Libyal Project: libscca ](https://github.com/libyal/libscca/blob/master/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc)

[Zena Forensics: A first look at Windows 10 Prefetch files](http://blog.digital-forensics.it/2015/06/a-first-look-at-windows-10-prefetch.html)

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
