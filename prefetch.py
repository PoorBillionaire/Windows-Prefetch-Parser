#!/usr/bin/python

# Copyright 2015 Adam Witt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contact: <accidentalassist@gmail.com>


from argparse import ArgumentParser
import binascii
import collections
import ctypes
from datetime import datetime,timedelta
import getpass
import json
import os
import struct
import sys


def convert_byte(onebyte):
	# Returns a Python int
	return struct.unpack_from("B", onebyte)[0]

def convert_word(twobytes):
    # Returns a Python int
    return struct.unpack_from("H", twobytes)[0]

def convert_dword(fourbytes):
    # Returns a Python int
    return struct.unpack_from("I", fourbytes)[0]

def convert_dwordlong(eightbytes):
    # Returns a Python int
    return struct.unpack_from("Q", eightbytes)[0]

def convert_double_dwordlong(eightbytes):
	# Returns a Python int
    return struct.unpack_from("2Q", eightbytes)[0]

def convert_string(nbytes, data):
    # Returns a string from binary data
    thestring = struct.unpack_from("{}s".format(str(nbytes)), data)[0]
    return thestring

def convert_timestamp(timestamp):
    # Timestamp is a Win32 FILETIME value
    # This function returns that value in a human-readable format

    return str(datetime(1601,1,1) + timedelta(microseconds=timestamp / 10.))

def build_filename(nbytes, data):
    # The prefetch filename is terminated by U+0000. This function Splits 
    # the bytes up on each side of \x00\x00 into an array and grabs the 
    # first element - the filename. After stripping ASCII NULL bytes, the
    # filename is returned
    fileNameData = convert_string(nbytes, data)
    fileName = fileNameData.split("\x00\x00")[0]
    return fileName.replace("\x00", "")


# The code in the class below was taken and then modified from Francesco 
# Picasso's w10pfdecomp.py script. This modification makes two simple changes:
#
#    - Wraps Francesco's logic in a Python class 
#    - Returns a bytearray of uncompressed data instead of writing it to a new 
#      file, like Francesco's original code did
#
# Author's name: Francesco "dfirfpi" Picasso
# Author's email: francesco.picasso@gmail.com
# Source: https://github.com/dfirfpi/hotoloti/blob/master/sas/w10pfdecomp.py
# License: http://www.apache.org/licenses/LICENSE-2.0

"""Python Windows-only utility to decompress MAM compressed files."""

class DecompressWin10(object):
    def __init__(self):
        pass

    def tohex(self, val, nbits):
        """Utility to convert (signed) integer to hex."""
        return hex((val + (1 << nbits)) % (1 << nbits))

    def decompress(self, infile):
        """Utility core."""

        NULL = ctypes.POINTER(ctypes.c_uint)()
        SIZE_T = ctypes.c_uint
        DWORD = ctypes.c_uint32
        USHORT = ctypes.c_uint16
        UCHAR  = ctypes.c_ubyte
        ULONG = ctypes.c_uint32

        # You must have at least Windows 8, or it should fail.
        try:
            RtlDecompressBufferEx = ctypes.windll.ntdll.RtlDecompressBufferEx
        except AttributeError:
            sys.exit('You must have Windows with version >=8.')

        RtlGetCompressionWorkSpaceSize = \
            ctypes.windll.ntdll.RtlGetCompressionWorkSpaceSize

        with open(infile, 'rb') as fin:
            header = fin.read(8)
            compressed = fin.read()

            signature, decompressed_size = struct.unpack('<LL', header)
            calgo = (signature & 0x0F000000) >> 24
            crcck = (signature & 0xF0000000) >> 28
            magic = signature & 0x00FFFFFF
            if magic != 0x004d414d :
                sys.exit('Wrong signature... wrong file?')

            if crcck:
                # I could have used RtlComputeCrc32.
                file_crc = struct.unpack('<L', compressed[:4])[0]
                crc = binascii.crc32(header)
                crc = binascii.crc32(struct.pack('<L',0), crc)
                compressed = compressed[4:]
                crc = binascii.crc32(compressed, crc)          
                if crc != file_crc:
                    sys.exit('{} Wrong file CRC {0:x} - {1:x}!'.format(infile, crc, file_crc))

            compressed_size = len(compressed)

            ntCompressBufferWorkSpaceSize = ULONG()
            ntCompressFragmentWorkSpaceSize = ULONG()

            ntstatus = RtlGetCompressionWorkSpaceSize(USHORT(calgo),
                ctypes.byref(ntCompressBufferWorkSpaceSize),
                ctypes.byref(ntCompressFragmentWorkSpaceSize))

            if ntstatus:
                sys.exit('Cannot get workspace size, err: {}'.format(
                    self.tohex(ntstatus, 32)))
                    
            ntCompressed = (UCHAR * compressed_size).from_buffer_copy(compressed)
            ntDecompressed = (UCHAR * decompressed_size)()
            ntFinalUncompressedSize = ULONG()
            ntWorkspace = (UCHAR * ntCompressFragmentWorkSpaceSize.value)()
            
            ntstatus = RtlDecompressBufferEx(
                USHORT(calgo),
                ctypes.byref(ntDecompressed),
                ULONG(decompressed_size),
                ctypes.byref(ntCompressed),
                ULONG(compressed_size),
                ctypes.byref(ntFinalUncompressedSize),
                ctypes.byref(ntWorkspace))

            if ntstatus:
                sys.exit('Decompression failed, err: {}'.format(
                    tohex(ntstatus, 32)))

            if ntFinalUncompressedSize.value != decompressed_size:
                sys.exit('Decompressed with a different size than original!')


        return bytearray(ntDecompressed)


class Universal(object):
    # This class defines methods which are universal for Prefetch across
    # all three versions: v17, v23, v26, and v30. These methods are compiled into
    # one "universal" class to avoid code repetition when not necessary

    def __init__(self, infile, offset=0, length=0):
        self.consume_header(infile)

    def consume_header(self, infile):
        # Parses the Prefetch file header, sets instance variables
        # to be used at a later time.

        h = infile.read(84)
        self.version = convert_dword(h[0:4])
        self.signature = convert_string(4, h[4:8])
        #header["pflength"] = convert_dword(h[12:16])
        self.fileName = build_filename(60, h[16:76])
        self.hash = hex(convert_dword(h[76:80]))

    def strings(self, infile, offset, length):
        # Returns a list of filename strings
        # These are the resources loaded at the application's runtime
        strings = []
        infile.seek(offset)
        stringsdata = convert_string(length, infile.read(length))
        splitstring = stringsdata.split("\x00\x00")
        
        for item in splitstring:
            strings.append(item.replace("\x00", ""))

        return strings


class prefetch_v17(object):
    def __init__(self, infile):
        self.universal = Universal(infile)
        self.fileName = self.universal.fileName
        self.fileinfo_v17(infile)
        self.strings = self.universal.strings(infile, offset=self.stringsOffset, length=self.stringsLength)
        self.volumes_v17(infile, self.volumesOffset)

    def fileinfo_v17(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Sets instance variables to be used later
        # Compatibility: v17
        infile.seek(84)
        i = infile.read(156)

        self.metricsOffset = convert_dword(i[0:4])
        self.metricsEntries = convert_dword(i[4:8])
        self.stringsOffset = convert_dword(i[16:20])
        self.stringsLength = convert_dword(i[20:24])
        self.volumesOffset = convert_dword(i[24:28])
        self.numberOfVolumesEntries = convert_dword(i[28:32])
        self.volumesLength = convert_dword(i[32:36])
        self.lastExecuted = convert_dwordlong(i[36:44])
        self.runCount = convert_dword(i[60:64])

    def volumes_v17(self, infile, offset):
	    # Volume information
	    # Compatibility: v17

        infile.seek(offset)
        v = infile.read(104)

        self.volumesOffset = convert_dword(v[0:4])
        self.volumesLength = convert_dword(v[4:8])
        self.volumeCreationTime = convert_timestamp(convert_dwordlong(v[8:16]))
        self.volumeSerialNumber = format(convert_dword(v[16:20]), "x")

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        infile.seek((infile.tell() - 104) + self.volumesOffset)

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        self.volumesPath = convert_string(self.volumesLength * 2, infile.read(self.volumesLength * 2))
        self.volumesPath =  self.volumesPath.replace("\x00", "")


class prefetch_v23(object):
    def __init__(self, infile):
        self.universal = Universal(infile)
        self.fileName = self.universal.fileName
        self.fileinfo_v23(infile)
        self.strings = self.universal.strings(infile, offset=self.stringsOffset, length=self.stringsLength)
        self.volumes(infile, self.volumesOffset)

    def fileinfo_v23(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Start of the 'info' section is after the header
        i = infile.read(156)

        self.metricsOffset = convert_dword(i[0:4])
        self.metricsEntries = convert_dword(i[4:8])
        self.tracehainsOffset = convert_dword(i[8:12])
        self.traceChainsEntries = convert_dword(i[12:16])
        self.stringsOffset = convert_dword(i[16:20])
        self.stringsLength = convert_dword(i[20:24])
        self.volumesOffset = convert_dword(i[24:28])
        self.volumesEntries = convert_dword(i[28:32])
        self.volumesLength = convert_dword(i[32:36])
        self.lastExecuted = convert_dwordlong(i[44:52])
        self.runCount = convert_dword(i[68:72])

    def volumes(self, infile, offset):
        # Volume information
        # Compatibility: v23, v26
        volumes = collections.OrderedDict({})
        infile.seek(offset)
        v = infile.read(104)

        self.volumesOffset = convert_dword(v[0:4])
        self.volumesLength = convert_dword(v[4:8])
        self.volumeCreationTime = convert_timestamp(convert_dwordlong(v[8:16]))
        self.volumeSerialNumber = format(convert_dword(v[16:20]), "x")

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        infile.seek(-104 + self.volumesOffset, 1)

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        self.volumesPath = convert_string(self.volumesLength * 2, infile.read(self.volumesLength * 2))
        self.volumesPath =  self.volumesPath.replace("\x00", "")


class prefetch_v26(object):
    def __init__(self, infile):
        self.universal = Universal(infile)
        self.fileName = self.universal.fileName
        self.fileinfo_v26(infile)
        self.strings = self.universal.strings(infile, offset=self.stringsOffset, length=self.stringsLength)
        self.volumes(infile, self.volumesOffset)

    def fileinfo_v26(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Start of the 'info' section is after the header
        infile.seek(84)
        # Information section is 156 bytes in length
        i = infile.read(224)

        self.metricsOffse = convert_dword(i[0:4])
        self.metricsEntries = convert_dword(i[4:8])
        self.traceChainsOffset = convert_dword(i[8:12])
        self.traceChainsEntries = convert_dword(i[12:16])
        self.stringsOffset = convert_dword(i[16:20])
        self.stringsLength = convert_dword(i[20:24])
        self.volumesOffset = convert_dword(i[24:28])
        self.volumesEntries = convert_dword(i[28:32])
        self.volumesLength = convert_dword(i[32:36])
        self.lastExecuted = convert_dwordlong(i[44:52])
        self.additionalExecutionTimestamps = struct.unpack("7Q", i[52:108])
        self.runCount = convert_dword(i[124:128])

    def volumes(self, infile, offset):
        # Volume information
        # Compatibility: v23, v26
        volumes = collections.OrderedDict({})
        infile.seek(offset)
        v = infile.read(104)

        self.volumesOffset = convert_dword(v[0:4])
        self.volumesLength = convert_dword(v[4:8])
        self.volumeCreationTime = convert_timestamp(convert_dwordlong(v[8:16]))
        self.volumeSerialNumber = format(convert_dword(v[16:20]), "x")

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        infile.seek(-104 + self.volumesOffset, 1)

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        self.volumesPath = convert_string(self.volumesLength * 2, infile.read(self.volumesLength * 2))
        self.volumesPath =  self.volumesPath.replace("\x00", "")


class Prefetch_v30(object):
    def __init__(self, infile):
        self.consume_header(infile)
        self.fileinfo_v30(infile)
        self.strings = self.strings(infile, offset=self.stringsOffset, length=self.stringsLength)
        self.volumes(infile, self.volumesOffset)

    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        # Compatibility: v30
        # Header is 84 bytes in length
        h = infile[0:84]

        self.version = convert_dword(h[0:4])
        self.signature = convert_string(4, h[4:8])
        self.fileName = build_filename(60, h[16:76])

    def fileinfo_v30(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Information section is 156 bytes in length
        i = infile[84:308]

        self.metricsOffset = convert_dword(i[0:4])
        self.metricsEntries = convert_dword(i[4:8])
        self.traceChainsOffset = convert_dword(i[8:12])
        self.traceChainsEntries = convert_dword(i[12:16])
        self.stringsOffset = convert_dword(i[16:20])
        self.stringsLength = convert_dword(i[20:24])
        self.volumesOffset = convert_dword(i[24:28])
        self.volumesEntries = convert_dword(i[28:32])
        self.volumesLength = convert_dword(i[32:36])
        self.lastExecuted = convert_dwordlong(i[44:52])
        self.additionalExecutionTimestamps = struct.unpack("7Q", i[52:108])
        self.runCount = convert_dword(i[124:128])

    def strings(self, infile, offset, length):
        # Returns an array of filename strings, from the "strings" section
        # of the Prefetch file
        strings = []
        s = infile[offset:offset + length]
        stringsdata = convert_string(length, s)
        splitstring = stringsdata.split("\x00\x00")
        
        for item in splitstring:
           strings.append(item.replace("\x00", ""))

        return strings

    def volumes(self, infile, offset):
        # Returns a dictionary object of the 'volumes' section
        v = infile[offset:offset + 96]

        self.volumesOffset = convert_dword(v[0:4])
        self.volumesLength = convert_dword(v[4:8])
        self.volumeCreationTime = convert_timestamp(convert_dwordlong(v[8:16]))
        self.volumeSerialNumber = format(convert_dword(v[16:20]), "x")

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        v = infile[(offset + self.volumesOffset) : (offset + self.volumesOffset + (self.volumesOffset * 2))]

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        self.volumesPath = convert_string(len(v), v)
        self.volumesPath =  self.volumesPath.replace("\x00", "")


def print_verbose(infile):
    # This function performs Prefetch file version detection
    # and prints parsed results to stdout

    with open(infile, "rb") as f:
        version = convert_dword(f.read(4))
        f.seek(-4, 1)

        if version == 17:
            p = prefetch_v17(f)
        elif version == 23:
            p = prefetch_v23(f)
        elif version == 26:
            p = prefetch_v26(f)
        else:
            compressedHeader = convert_string(3, f.read(3))
            if compressedHeader == "MAM":
                d = DecompressWin10()
                decompressed = d.decompress(infile)
                p = Prefetch_v30(decompressed)
            else:
                sys.exit("[ - ] Unknown file type")
    
    banner = "=" * (len(p.fileName) + 2)
    print "\n{0}\n{1}\n{0}\n".format(banner, p.fileName)
    print "Run count: {}".format(p.runCount)
    print "Last executed: {}".format(convert_timestamp(p.lastExecuted))

    if hasattr(p, "additionalExecutionTimestamps"):
        print "Additional execution timestamp(s):"
        for item in p.additionalExecutionTimestamps:
            if item:
                print "    {}".format(convert_timestamp(item))

    print "\nVolume path: {}".format(p.volumesPath)
    print "Volume serial number {}".format(p.volumeSerialNumber)
    print "\nResources loaded:\n"

    count = 1

    for item in p.strings:
        if item != p.strings[-1]:
            if count > 999:
                print "{}: {}".format(count, item)
            if count > 99:
                print "{}:  {}".format(count, item)                            
            elif count > 9:
                print "{}:   {}".format(count, item)
            else:
                print "{}:    {}".format(count, item)
        count += 1

def sortByExecutionTime(directory):
    # This function returns the filename and last execution time of a given Prefetch file
    # This function is broken out be cause it is used when sorting last executing times
    # for a directory of prefetch files (-e functionality)

    files = {}

    for i in os.listdir(directory):
        if i.endswith(".pf"):
            if os.path.getsize(directory + i) > 0:
                with open(directory + i, "rb") as f:
                    version = convert_dword(f.read(4))
                    f.seek(-4, 1)

                    if version == 17:
                        p = prefetch_v17(f)
                        files.update({p.fileName : p.lastExecuted})
                    elif version == 23:
                        p = prefetch_v23(f)
                        files.update({p.fileName : p.lastExecuted})
                    elif version == 26:
                        p = prefetch_v26(f)
                        files.update({p.fileName : p.lastExecuted})
                    else:
                        compressedHeader = convert_string(3, f.read(3))
                        f.seek(-3, 1)
                        if compressedHeader == "MAM":
                            d = DecompressWin10()
                            decompressed = d.decompress(directory + i)
                            p = Prefetch_v30(decompressed)
                            files.update({p.fileName : p.lastExecuted})
                        else:
                            sys.exit("[ - ] Unknown file type")

    sortedfiles = [(k,v) for v,k in sorted([(v,k) for k,v in files.items()], reverse=True)]

    for item in sortedfiles:
        if item[1] == "Zero byte Prefetch file":
            print item[1] + " - " + item[0]
        else:
            print convert_timestamp(item[1]) + " - " + item[0]


def zeroByteFileDetected(infile):
    # Function to handle output for zero-byte Prefetch files
    banner = "=" * (len(infile) + 2)
    print "\n{0}\n{1}\n{0}\n".format(banner, infile)
    print "[ - ] This file is zero bytes in length and cannot be parsed"



def main():

    p = ArgumentParser()
    p.add_argument("-d", "--directory", help="Parse a directory of Prefetch files")
    p.add_argument("-e", "--executed", help="Provide high-level information, sorted by last executed time")
    p.add_argument("-f", "--file", help="Parse a given Prefetch file")
    p.add_argument("-z", "--zero", help="Identify empty prefetch files")
    args = p.parse_args()


    if args.file:
        if os.path.getsize(args.file) > 0:
            print_verbose(args.file)
        else:
            zeroByteFileDetected(args.file)

    elif args.directory:
        if not (args.directory.endswith("/") or args.directory.endswith("\\")):
            sys.exit("\n[ - ] When enumerating a directory, add a trailing slash\n")
        
        for pfile in os.listdir(args.directory):
            if pfile.endswith(".pf"):
                if os.path.getsize(args.directory + pfile) > 0:
                    print_verbose(args.directory + pfile)
                else:
                    zeroByteFileDetected(pfile)
    
    elif args.executed:
        if (args.executed.endswith("/") or args.executed.endswith("\\")):
            if os.path.isdir(args.executed):
                sortByExecutionTime(args.executed)

            else:
                sys.exit("[ - ] Given path is not a directory")
        else:
            sys.exit("\n[ - ] When enumerating a directory, add a trailing slash\n")

    elif args.zero:
        emptyfiles = []
        if not (args.zero.endswith("/") or args.zero.endswith("\\")):
            sys.exit("\n[ - ] When enumerating a directory, add a trailing slash\n")

        for i in os.listdir(args.zero):
            if i.endswith(".pf"):
                if os.path.getsize(args.zero + i) == 0:
                    emptyfiles.append(i)

        if emptyfiles:
            message = "Zero-byte Prefetch Files"
            border = "=" * (len(message) + 2)
            print "\n{0}\n{1}\n{0}\n".format(border,message)

            for item in emptyfiles:
                print "[ - ] {}".format(item)
            print ""

        else:
            print "\n[ + ] {} does not contain any zero-byte Prefetch files.\n".format(args.zero)


main()
