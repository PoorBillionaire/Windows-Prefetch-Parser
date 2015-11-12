
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
    #.replace("\x00", "")

def convert_timestamp(timestamp):
    # Timestamp is a Win32 FILETIME value
    # This function returns that value in a human-readable format

    return str(datetime(1601,1,1) + timedelta(microseconds=timestamp / 10.))

def build_filename(nbytes, data):
    # The prefetch filename is terminated by U+0000. This function Splits 
    # the bytes up on each side of \x00\x00 into an array and grabs the 
    # first element - the filename. After stripping ASCII NULL bytes, the
    # filename is returned
    thebytes = convert_string(nbytes, data)
    filename = thebytes.split("\x00\x00")[0]
    return filename.replace("\x00", "")


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
                    sys.exit('Wrong file CRC {0:x} - {1:x}!'.format(crc, file_crc))

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
                print 'Decompressed with a different size than original!'


            return bytearray(ntDecompressed)




class Universal(object):
    # This class defines methods which are universal for Prefetch across
    # all three versions: v17, v23, and v26. These methods are compiled into
    # one "universal" class to avoid code repetition when not necessary

    def __init__(self, infile, offset):
        pass

    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        # Compatibility: v17, v23, v26
        header = collections.OrderedDict({})
        # Header is 84 bytes in length
        h = infile.read(84)

        header["version"] = convert_dword(h[0:4])
        header["signature"] = convert_string(4, h[4:8])
        header["unknown1"] = convert_dword(h[8:12])
        header["pflength"] = convert_dword(h[12:16])
        header["filename"] = build_filename(60, h[16:76])
        header["pfhash"] = hex(convert_dword(h[76:80]))
        header["unknown2"] = convert_dword(h[80:84])

        return header

    def trace(self, infile, offset):
        # Section B: Trace chains array
        # Compatibility: v17, v23, v26
    
        trace = collections.OrderedDict({})
        infile.seek(offset)
        t = infile.read(12)

        trace["nextarray"] = convert_dword(t[0:4])
        trace["blocksloaded"] = convert_dword(t[4:8])
        trace["unknown1"] = convert_byte(t[8:9])
        trace["unknown2"] = convert_byte(t[9:10])
        trace["unknown3"] = convert_word(t[10:12])

        return trace

    def strings(self, infile, offset, length):
        # Filename strings
        # Compatibility: v17, v23, v26
        strings = []
        infile.seek(offset)
        stringsdata = convert_string(length, infile.read(length))
        splitstring = stringsdata.split("\x00\x00")
        
        for item in splitstring:
            strings.append(item.replace("\x00", ""))

        return strings

    def fileref(self, infile, volumesoffset, filerefoffset, length):
        filereferences = collections.OrderedDict({})
        infile.seek(volumesoffset + filerefoffset)
        r = infile.read(length)

        filereferences["unknown1"] = convert_dword(r[0:4])
        filereferences["count"] = convert_dword(r[4:8])
        filereferences["array"] = r[8:]

        return filereferences


    def directorystrings(self, infile, volumesoffset, diroffset, strcount):
        infile.seek(volumesoffset + diroffset)
        count = 0
        strings = []

        while count < strcount:
            characters = convert_word(infile.read(2))
            directorystr = convert_string((characters * 2) + 2, infile.read((characters * 2) + 2))
            directorystr = directorystr.replace("\x00", "")
            strings.append(directorystr)
            count += 1

        return strings



class prefetch_v17(object):
    def __init__(self, infile, *offset):
        self.universal = Universal(infile, offset)

        self.metricsoffset = None
        self.tracechainsoffset = None
        self.stringsoffset = None
        self.stringslength = None
        self.volumesoffset = None
        self.volumesentries = None
        self.volumeslength = None
        self.offsetE = None
        self.lengthE = None
        self.offsetF = None
        self.stringcountF = None

    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        return self.universal.consume_header(infile)


    def fileinfo_v17(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Compatibility: v17
        info = collections.OrderedDict({})
        # Information section is 156 bytes in length
        i = infile.read(156)

        info["metricsoffset"] = convert_dword(i[0:4])
        info["metricsentries"] = convert_dword(i[4:8])
        info["tracechains_offset"] = convert_dword(i[8:12])
        info["tracechains_entries"] = convert_dword(i[12:16])
        info["stringsoffset"] = convert_dword(i[16:20])
        info["stringslength"] = convert_dword(i[20:24])
        info["volumesoffset"] = convert_dword(i[24:28])
        info["volumesentries"] = convert_dword(i[28:32])
        info["volumeslength"] = convert_dword(i[32:36])
        info["filetime"] = convert_timestamp(convert_dwordlong(i[36:44]))
        info["unknown1"] = convert_double_dwordlong(i[44:60])
        info["runcount"] = convert_dword(i[60:64])
        info["unknown3"] = convert_dword(i[64:68])

        self.metricsoffset = info["metricsoffset"]
        self.tracechainsoffset = info["tracechains_offset"]
        self.stringsoffset = info["stringsoffset"]
        self.stringslength = info["stringslength"]
        self.volumesoffset = info["volumesoffset"]
        self.volumesentries = info["volumesentries"]
        self.volumeslength = info["volumeslength"]

        return info

    def metrics_v17(self, infile):
        # Section A: Metrics array
        # Compatibility: v17

        metrics = collections.OrderedDict({})
        infile.seek(self.metricsoffset)
        m = infile.read(20)

        metrics["starttime"] = convert_dword(m[0:4])
        metrics["duration"] = convert_dword(m[4:8])
        # Filename offset is relative to the start of the filename string section (section C)
        metrics["filenamestring_offset"] = convert_dword(m[12:16])
        metrics["unknown"] = convert_dword(m[16:20])

        return metrics

    def trace(self, infile, offset):
        # Returns the Prefetch file header as a Python dictionary object
        return self.universal.trace(infile, offset)

    def strings(self, infile, offset, length):
        # Filename strings
        return self.universal.strings(infile, offset, length)

    def volumes_v17(self, infile, offset):
	    # Volume information
	    # Compatibility: v17

        volumes = collections.OrderedDict({})
        volumes = collections.OrderedDict({})
        infile.seek(offset)
        v = infile.read(104)

        volumes["vol_offset"] = convert_dword(v[0:4])
        volumes["vol_length"] = convert_dword(v[4:8])
        volumes["vol_createtime"] = convert_timestamp(convert_dwordlong(v[8:16]))
        volumes["vol_serialnumber"] = format(convert_dword(v[16:20]), "x")
        volumes["sectionE_offset"] = convert_dword(v[20:24])
        volumes["sectionE_length"] = convert_dword(v[24:28])
        volumes["sectionF_offset"] = convert_dword(v[28:32])
        volumes["sectionF_stringcount"] = convert_dword(v[32:36])
        volumes["unknown1"] = convert_dword(v[36:40])


        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        infile.seek((infile.tell() - 104) + volumes["vol_offset"])

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        volumes["volpath"] = convert_string(volumes["vol_length"] * 2, infile.read(volumes["vol_length"] * 2))
        volumes["volpath"] =  volumes["volpath"].replace("\x00", "")

        return volumes

     
    def fileref(self, infile, volumesoffset, filerefoffset, length):
        return self.universal.fileref(infile, offset)


    def directorystrings(self, infile, volumesoffset, diroffset, strcount):
        return self.universal.directorystrings(infile, volumesoffset, diroffset, strcount)



class prefetch_v23(object):
    def __init__(self, infile, *offset):
        self.universal = Universal(infile, offset)

        self.metricsoffset = None
        self.tracechainsoffset = None
        self.stringsoffset = None
        self.stringslength = None
        self.volumesoffset = None
        self.volumesentries = None
        self.volumeslength = None
        self.offsetE = None
        self.lengthE = None
        self.offsetF = None
        self.stringcountF = None


    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        # Compatibility: v17, v23, v26
        return self.universal.consume_header(infile)

    def fileinfo_v23(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Compatibility: v23

        info = collections.OrderedDict({})

        # Start of the 'info' section is after the header
        infile.seek(84)
        # Information section is 156 bytes in length
        i = infile.read(156)

        info["metricsoffset"] = convert_dword(i[0:4])
        info["metricsentries"] = convert_dword(i[4:8])
        info["tracechains_offset"] = convert_dword(i[8:12])
        info["tracechains_entries"] = convert_dword(i[12:16])
        info["stringsoffset"] = convert_dword(i[16:20])
        info["stringslength"] = convert_dword(i[20:24])
        info["volumesoffset"] = convert_dword(i[24:28])
        info["volumesentries"] = convert_dword(i[28:32])
        info["volumeslength"] = convert_dword(i[32:36])
        info["unknown1"] = convert_dwordlong(i[36:44])
        info["filetime"] = convert_timestamp(convert_dwordlong(i[44:52]))
        info["unknown2"] = convert_double_dwordlong(i[52:68])
        info["runcount"] = convert_dword(i[68:72])
        info["unknown3"] = convert_dword(i[72:76])
        info["unknown4"] = struct.unpack("20I", i[76:156])[0]

        self.metricsoffset = info["metricsoffset"]
        self.tracechainsoffset = info["tracechains_offset"]
        self.stringsoffset = info["stringsoffset"]
        self.stringslength = info["stringslength"]
        self.volumesoffset = info["volumesoffset"]
        self.volumesentries = info["volumesentries"]
        self.volumeslength = info["volumeslength"]

        return info

    def metrics(self, infile, offset):
        # Section A: Metrics array
        # Compatibility: v23, v26

        metrics = collections.OrderedDict({})
        infile.seek(offset)
        m = infile.read(32)

        metrics["starttime"] = convert_dword(m[0:4])
        metrics["duration"] = convert_dword(m[4:8])
        metrics["average"] = convert_dword(m[8:12])
        # Filename offset is relative to the start of the filename string section (section C)
        metrics["filenamestring_offset"] = convert_dword(m[12:16])
        metrics["filenamesstring_nocharacters"] = convert_dword(m[16:20])
        metrics["unknown"] = convert_dword(m[20:24])
        metrics["ntfsreference"] = convert_dwordlong(m[24:32])

        return metrics

    def trace(self, infile, offset):
        # Returns the Prefetch Trace section as a Python dictionary object
        return self.universal.trace(infile, offset)


    def strings(self, infile, offset, length):
        # Returns the Prefetch Strings section as a Python dictionary object
        return self.universal.strings(infile, offset, length)


    def volumes(self, infile, offset):
        # Volume information
        # Compatibility: v23, v26
        volumes = collections.OrderedDict({})
        infile.seek(offset)
        v = infile.read(104)

        volumes["vol_offset"] = convert_dword(v[0:4])
        volumes["vol_length"] = convert_dword(v[4:8])
        volumes["vol_createtime"] = convert_timestamp(convert_dwordlong(v[8:16]))
        volumes["vol_serialnumber"] = format(convert_dword(v[16:20]), "x")
        volumes["sectionE_offset"] = convert_dword(v[20:24])
        volumes["sectionE_length"] = convert_dword(v[24:28])
        volumes["sectionF_offset"] = convert_dword(v[28:32])
        volumes["sectionF_stringcount"] = convert_dword(v[32:36])
        volumes["unknown1"] = convert_dword(v[36:40])
        volumes["unknown2"] = struct.unpack("7I", v[40:68])
        volumes["unknown3"] = convert_dword(v[68:72])
        volumes["unknown4"] = struct.unpack("7I", v[72:100])
        volumes["unknown5"] = convert_dword(v[100:104])

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        infile.seek(-104 + volumes["vol_offset"], 1)

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        volumes["volpath"] = convert_string(volumes["vol_length"] * 2, infile.read(volumes["vol_length"] * 2))
        volumes["volpath"] =  volumes["volpath"].replace("\x00", "")

        # Setting class instance variables for access by methods later on
        self.offsetE = volumes["sectionE_offset"]
        self.lengthE = volumes["sectionE_length"]
        self.offsetF = volumes["sectionF_offset"]
        self.stringcountF = volumes["sectionF_stringcount"]

        return volumes


    def fileref(self, infile, volumesoffset, filerefoffset, length):
        return self.universal.fileref(infile, volumesoffset, filerefoffset, length)


    def directorystrings(self, infile, volumesoffset, diroffset, strcount):
    	print volumesoffset
        return self.universal.directorystrings(infile, volumesoffset, diroffset, strcount)


class prefetch_v26(object):
    def __init__(self, infile, *offset):
        self.universal = Universal(infile, offset)
        self.v23compatible = prefetch_v23(infile, offset)

        self.metricsoffset = None
        self.tracechainsoffset = None
        self.stringsoffset = None
        self.stringslength = None
        self.volumesoffset = None
        self.volumesentries = None
        self.volumeslength = None
        self.offsetE = None
        self.lengthE = None
        self.offsetF = None
        self.stringcountF = None

    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        return self.universal.consume_header(infile)


    def fileinfo_v26(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Compatibility: v26

        info = collections.OrderedDict({})

        # Start of the 'info' section is after the header
        infile.seek(84)
        # Information section is 156 bytes in length
        i = infile.read(224)

        info["metricsoffset"] = convert_dword(i[0:4])
        info["metricsentries"] = convert_dword(i[4:8])
        info["tracechains_offset"] = convert_dword(i[8:12])
        info["tracechains_entries"] = convert_dword(i[12:16])
        info["stringsoffset"] = convert_dword(i[16:20])
        info["stringslength"] = convert_dword(i[20:24])
        info["volumesoffset"] = convert_dword(i[24:28])
        info["volumesentries"] = convert_dword(i[28:32])
        info["volumeslength"] = convert_dword(i[32:36])
        info["unknown1"] = convert_dwordlong(i[36:44])
        info["filetime0"] = convert_timestamp(convert_dwordlong(i[44:52]))
        info["filetime1"] = convert_timestamp(struct.unpack("7Q", i[52:108])[0])
        info["unknown2"] = convert_double_dwordlong(i[108:124])
        info["runcount"] = convert_dword(i[124:128])
        info["unknown3"] = convert_dword(i[128:132])
        info["unknown4"] = convert_dword(i[132:136])
        info["unknown5"] = struct.unpack("11Q", i[136:224])

        self.metricsoffset = info["metricsoffset"]
        self.tracechainsoffset = info["tracechains_offset"]
        self.stringsoffset = info["stringsoffset"]
        self.stringslength = info["stringslength"]
        self.volumesoffset = info["volumesoffset"]
        self.volumesentries = info["volumesentries"]
        self.volumeslength = info["volumeslength"]

        return info

    def metrics(self, infile):
        # Section A: Metrics array
        # Compatibility: v23, v26
        return self.v23compatible.metrics(infile)


    def trace(self, infile, offset):
        # Section B: Trace chains array
        return self.universal.trace(infile, offset)

    def strings(self, infile, offset, length):
        # Filename strings
        return self.universal.strings(infile, offset, length)

    def volumes(self, infile, offset):
        # Volume information
        return self.v23compatible.volumes(infile, offset)

    def fileref(self, infile, volumesoffset, filerefoffset, length):
        return self.universal.fileref(infile, volumesoffset, filerefoffset, length)

    def directorystrings(self, infile, volumesoffset, diroffset, strcount):
        return self.universal.directorystrings(infile, volumesoffset, diroffset, strcount)



class Prefetch_v30(object):
    def __init__(self):
        pass

        self.metricsoffset = None
        self.tracechainsoffset = None
        self.stringsoffset = None
        self.stringslength = None
        self.volumesoffset = None
        self.volumesentries = None
        self.volumeslength = None
        self.offsetE = None
        self.lengthE = None
        self.offsetF = None
        self.stringcountF = None

    def consume_header(self, infile):
        # Returns the Prefetch file header as a Python dictionary object
        # Compatibility: v30
        header = collections.OrderedDict({})
        # Header is 84 bytes in length
        h = infile[0:84]

        header["version"] = convert_dword(h[0:4])
        header["signature"] = convert_string(4, h[4:8])
        header["unknown1"] = convert_dword(h[8:12])
        header["pflength"] = convert_dword(h[12:16])
        header["filename"] = build_filename(60, h[16:76])
        header["pfhash"] = hex(convert_dword(h[76:80]))
        header["unknown2"] = convert_dword(h[80:84])

        return header        

    def fileinfo_v30(self, infile):
        # Parse through the 'File Information' portion of Prefetch file
        # Compatibility: v26

        info = collections.OrderedDict({})
        # Information section is 156 bytes in length
        i = infile[84:308]

        info["metricsoffset"] = convert_dword(i[0:4])
        info["metricsentries"] = convert_dword(i[4:8])
        info["tracechains_offset"] = convert_dword(i[8:12])
        info["tracechains_entries"] = convert_dword(i[12:16])
        info["stringsoffset"] = convert_dword(i[16:20])
        info["stringslength"] = convert_dword(i[20:24])
        info["volumesoffset"] = convert_dword(i[24:28])
        info["volumesentries"] = convert_dword(i[28:32])
        info["volumeslength"] = convert_dword(i[32:36])
        info["unknown1"] = convert_dwordlong(i[36:44])
        info["filetime0"] = convert_timestamp(convert_dwordlong(i[44:52]))
        info["filetime1"] = convert_timestamp(struct.unpack("7Q", i[52:108])[0])
        info["unknown2"] = convert_double_dwordlong(i[108:124])
        info["runcount"] = convert_dword(i[124:128])
        info["unknown3"] = convert_dword(i[128:132])
        info["unknown4"] = convert_dword(i[132:136])
        info["unknown5"] = struct.unpack("11Q", i[136:224])

        self.metricsoffset = info["metricsoffset"]
        self.tracechainsoffset = info["tracechains_offset"]
        self.stringsoffset = info["stringsoffset"]
        self.stringslength = info["stringslength"]
        self.volumesoffset = info["volumesoffset"]
        self.volumesentries = info["volumesentries"]
        self.volumeslength = info["volumeslength"]

        return info

    def metrics(self, infile, offset):
        # Section A: Metrics array
        metrics = collections.OrderedDict({})
        m = infile[offset:offset + 32]

        metrics["starttime"] = convert_dword(m[0:4])
        metrics["duration"] = convert_dword(m[4:8])
        metrics["average"] = convert_dword(m[8:12])
        # Filename offset is relative to the start of the filename string section (section C)
        metrics["filenamestring_offset"] = convert_dword(m[12:16])
        metrics["filenamesstring_nocharacters"] = convert_dword(m[16:20])
        metrics["unknown"] = convert_dword(m[20:24])
        metrics["ntfsreference"] = convert_dwordlong(m[24:32])

        return metrics

    def strings(self, infile, offset, length):
        # Filename strings
        strings = []
        s = infile[offset:offset + length]
        stringsdata = convert_string(length, s)
        splitstring = stringsdata.split("\x00\x00")
        
        for item in splitstring:
            strings.append(item.replace("\x00", ""))

        return strings


    def volumes(self, infile, offset):
        # Volume information
        volumes = collections.OrderedDict({})
        v = infile[offset:offset + 96]

        volumes["vol_offset"] = convert_dword(v[0:4])
        volumes["vol_length"] = convert_dword(v[4:8])
        volumes["vol_createtime"] = convert_timestamp(convert_dwordlong(v[8:16]))
        volumes["vol_serialnumber"] = format(convert_dword(v[16:20]), "x")
        volumes["sectionE_offset"] = convert_dword(v[20:24])
        volumes["sectionE_length"] = convert_dword(v[24:28])
        volumes["sectionF_offset"] = convert_dword(v[28:32])
        volumes["sectionF_stringcount"] = convert_dword(v[32:36])
        volumes["unknown1"] = convert_dword(v[36:40])
        volumes["unknown2"] = struct.unpack("6I", v[40:64])
        volumes["unknown3"] = convert_dword(v[64:68])
        volumes["unknown4"] = struct.unpack("6I", v[68:92])
        volumes["unknown5"] = convert_dword(v[92:96])

        # Volume path offset is relative to the start of section D
        # This piece seeks back to the start of section D, and then
        # seeks to the volume path from that point
        v = infile[(offset + volumes["vol_offset"]) : (offset + volumes["vol_offset"] + (volumes["vol_length"] * 2))]

        # vol_length is the number of characters in the volpath string
        # The volume path string is UTF-16, which means each character
        # consumes two bytes. vol_length * 2 account for this
        volumes["volpath"] = convert_string(len(v), v)
        volumes["volpath"] =  volumes["volpath"].replace("\x00", "")

        return volumes



def main():

    p = ArgumentParser()
    p.add_argument("pfile", help="Parse a given Prefetch file")
    args = p.parse_args()


    if args.file:    

        if not os.path.exists(args.file):
            sys.exit("[ - ] File not found")
        else:
            with open(args.file, "rb") as f:
                version = convert_dword(f.read(4))


        if version == 17:
            with open(args.file, "rb") as f:
                p = prefetch_v17(f)

                header = p.consume_header(f)
                info = p.fileinfo_v17(f)
                strings = p.strings(f, p.stringsoffset, p.stringslength)
                volumes = p.volumes_v17(f, p.volumesoffset)

                print "\nFilename: {}".format(header["filename"])
                print "Volume path: {}".format(volumes["volpath"])
                print "Run count: {}\n".format(info["runcount"])
                print "Last executed: {}\n".format(info["filetime"])

                count = 1
                for item in strings:
                    if item != strings[-1]:
                        if count > 9:
                            print "{}: {}".format(count, item)
                        else:
                            print "{}:  {}".format(count, item)
                    count += 1


        elif version == 23:
            with open(args.file, "rb") as f:
                p = prefetch_v23(f)
                header = p.consume_header(f)
                info = p.fileinfo_v23(f)
                #metrics = p.metrics(f, p.metricsoffset)
                #trace = p.trace(f, p.tracechainsoffset)
                strings = p.strings(f, p.stringsoffset, p.stringslength)
                volumes = p.volumes(f, p.volumesoffset)
                #fileref = p.fileref(f, p.volumesoffset, p.offsetE, p.lengthE)
                #dirref = p.directorystrings(f, p.volumesoffset, p.offsetF, p.stringcountF)

                print "\nFilename: {}".format(header["filename"])
                print "Last executed: {}".format(info["filetime"])
                print "Run count: {}\n".format(info["runcount"])
                print "Volume path: {}".format(volumes["volpath"])
                print "Volume serial number {}\n".format(volumes["vol_serialnumber"])


                count = 1
                for item in strings:
                    if item != strings[-1]:
                        if count > 9:
                            print "{}: {}".format(count, item)
                        else:
                            print "{}:  {}".format(count, item)
                    count += 1


        elif version == 26:
            with open(args.file, "rb") as f:
                p = prefetch_v26(f)
                header = p.consume_header(f)
                info = p.fileinfo_v26(f)
                strings = p.strings(f, p.stringsoffset, p.stringslength)
                volumes = p.volumes(f, p.volumesoffset)

                print "\nFilename: {}".format(header["filename"])
                print "Last executed: {}".format(info["filetime0"])
                print "Run count: {}\n".format(info["runcount"])
                print "Volume path: {}".format(volumes["volpath"])
                print "Volume serial number {}\n".format(volumes["vol_serialnumber"])

                count = 1
                for item in strings:
                    if item != strings[-1]:
                        if count > 9:
                            print "{}: {}".format(count, item)
                        else:
                            print "{}:  {}".format(count, item)
                    count += 1

        else:
            with open(args.file, "rb") as f:
                if not convert_string(3, f.read(3)) == "MAM":
                    sys.exit("[ - ] Unknown Prefetch file type")
                              
            d = DecompressWin10()
            decompressed = d.decompress(args.file)

            p = Prefetch_v30()
            header = p.consume_header(decompressed)
            info = p.fileinfo_v30(decompressed)
            metrics = p.metrics(decompressed, info["metricsoffset"])
            strings = p.strings(decompressed, p.stringsoffset, p.stringslength)
            volumes = p.volumes(decompressed, p.volumesoffset)


            print "\nFilename: {}".format(header["filename"])
            print "Last executed: {}".format(info["filetime0"])
            print "Run count: {}\n".format(info["runcount"])
            print "Volume path: {}".format(volumes["volpath"])
            print "Volume serial number {}\n".format(volumes["vol_serialnumber"])

            count = 1
            for item in strings:
                if item != strings[-1]:
                    if count > 9:
                        print "{}: {}".format(count, item)
                    else:
                        print "{}:  {}".format(count, item)
                count += 1


main()
