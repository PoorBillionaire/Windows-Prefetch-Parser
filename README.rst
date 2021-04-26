Windows-Prefetch-Parser
========================
Python script created to parse Windows Prefetch files: Supports XP - Windows 10 Prefetch files

Description
------------
The Windows application prefetch mechanism  was put in place to offer performance benefits when launching applications. It just so happens to be one of the more beneficial forensic artifacts regarding evidence of applicaiton execution as well. prefetch.py provides functionality for parsing prefetch files for all current prefetch file versions: 17, 23, 26, and 30.

Features
---------
* Specify a single prefetch file or a directory of prefetch files
* CSV output support
* (Limited) Windows 10 support - Windows 10 prefetch files must be parsed from a Windows 8+ workstation


Command-Line Options
---------------------
For now, prefetch.py requires only one command-line option: ``--file`` can specify a single Prefetch file, or a directory of Prefetch files to parse: 

::

    dev@computer:~$ ./prefetch.py -h
    usage: prefetch.py [-h] [-c] [-f FILE]
    
    optional arguments:
      -h, --help            show this help message and exit
      -c, --csv             Present results in CSV format
      -f FILE, --file FILE  Parse a given Prefetch file

Single Prefetch File
---------------------

Using the ``--file / -f`` switch with a single prefetch file results in the output below:

::

    dev@computer:~$ python prefetch.py -f CMD.EXE-4A81B364.pf

    =====================
    CMD.EXE-4A81B364.pf
    =====================
    
    Executable Name: CMD.EXE
    
    Run count: 2
    Last Executed: 2016-01-16 20:26:42.515108
    
    Volume Information:
        Volume Name: \DEVICE\HARDDISKVOLUME2
        Creation Date: 2016-01-16 21:15:18.109374
        Serial Number: 88008c2f
    
    Directory Strings:
        \DEVICE\HARDDISKVOLUME2\WINDOWS
        \DEVICE\HARDDISKVOLUME2\WINDOWS\BRANDING
        \DEVICE\HARDDISKVOLUME2\WINDOWS\BRANDING\BASEBRD
        \DEVICE\HARDDISKVOLUME2\WINDOWS\GLOBALIZATION
        \DEVICE\HARDDISKVOLUME2\WINDOWS\GLOBALIZATION\SORTING
        \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32
    
    Resources loaded:

    1:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\NTDLL.DLL
    2:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\KERNEL32.DLL
    3:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\APISETSCHEMA.DLL
    4:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\KERNELBASE.DLL
    5:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\LOCALE.NLS
    6:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\CMD.EXE
    7:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\MSVCRT.DLL
    8:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\WINBRAND.DLL
    9:    \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\USER32.DLL
    10:   \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\GDI32.DLL
    11:   \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\LPK.DLL
    12:   \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\USP10.DLL
    13:   \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\IMM32.DLL
    14:   \DEVICE\HARDDISKVOLUME2\WINDOWS\SYSTEM32\MSCTF.DLL
    15:   \DEVICE\HARDDISKVOLUME2\WINDOWS\BRANDING\BASEBRD\BASEBRD.DLL
    16:   \DEVICE\HARDDISKVOLUME2\WINDOWS\GLOBALIZATION\SORTING\SORTDEFAULT.NLS

Muliple Prefetch Files
-----------------------

Use the same syntax as above, but point the script to a directory of Prefetch files.

CSV Format
-----------

Using the ``--csv / -c`` flag will provide results in CSV format:

::

    Last Executed, Executable Name, Run Count
    2016-01-20 16:01:27.680128, ADOBEIPCBROKER.EXE-c8d02fab, 1
    2016-01-20 16:59:42.077480, CREATIVE CLOUD UNINSTALLER.EX-216b8ea8, 1
    2016-01-19 18:07:18.101626, MSIEXEC.EXE-a2d55cb6, 37237
    2016-01-20 16:11:15.818394, ACRODIST.EXE-782bc2b2, 1


References
-----------

This project would not have been possible without the work of others much smarter than I. The prefetch file format is not officially documented by Microsoft and has been understood through reverse engineering, and trial-and-error. 

Additionally, Without the excellent work by Francesco Picasso in understanding the Windows 10 prefetch compression method, I would not have been able to get Windows 10 parsed here. I use a modified version of his decompression script in prefetch.py. Francesco's original script can be found at the link below:

`w10pfdecomp.py <https://github.com/dfirfpi/hotoloti/blob/master/sas/w10pfdecomp.py>`_

To gain a better understanding of the prefetch file format, check out the following resources; which were all used as references for the creation of my script:

`ForensicsWiki: Windows Prefetch File Format <http://www.forensicswiki.org/wiki/Windows_Prefetch_File_Format>`_

`Libyal Project: libscca <https://github.com/libyal/libscca/blob/master/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc>`_

`Zena Forensics: A first look at Windows 10 Prefetch files <http://blog.digital-forensics.it/2015/06/a-first-look-at-windows-10-prefetch.html>`_

