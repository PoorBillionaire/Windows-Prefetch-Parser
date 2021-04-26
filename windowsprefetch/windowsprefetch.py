# Copyright 2021 Adam Witt
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


import os
import ntpath
import struct
import tempfile
from datetime import datetime,timedelta
from windowsprefetch.utils import DecompressWin10


class Prefetch(object):
    def __init__(self, infile):
        self.pFileName = infile

        with open(infile, "rb") as f:
            if f.read(3).decode("ASCII") == "MAM":
                f.close()
                d = DecompressWin10()
                decompressed = d.decompress(infile)
                t = tempfile.mkstemp()
                with open(t[1], "wb+") as f:
                    f.write(decompressed)
                    f.seek(0)

                    self.parseHeader(f)
                    self.fileInformation26(f)
                    self.metricsArray23(f)
                    self.traceChainsArray30(f)
                    self.volumeInformation30(f)
                    self.getTimeStamps(self.lastRunTime)
                    self.directoryStrings(f)
                    self.getFilenameStrings(f)
                    return

        with open(infile, "rb") as f:
            self.parseHeader(f)
            
            if self.version == 17:
                self.fileInformation17(f)
                self.metricsArray17(f)
                self.traceChainsArray17(f)
                self.volumeInformation17(f)
                self.getTimeStamps(self.lastRunTime)
                self.directoryStrings(f)
            
            elif self.version == 23:
                self.fileInformation23(f)
                self.metricsArray23(f)
                self.traceChainsArray17(f)
                self.volumeInformation23(f)
                self.getTimeStamps(self.lastRunTime)
                self.directoryStrings(f)

            elif self.version == 26:
                self.fileInformation26(f)
                self.metricsArray23(f)
                self.traceChainsArray17(f)
                self.volumeInformation23(f)
                self.getTimeStamps(self.lastRunTime)
                self.directoryStrings(f)

            self.getFilenameStrings(f)

    def parseHeader(self, infile):
        # Parse the file header
        # 84 bytes
        self.version = struct.unpack_from("I", infile.read(4))[0]
        self.signature = struct.unpack_from("I", infile.read(4))[0]
        unknown0 = struct.unpack_from("I", infile.read(4))[0]
        self.fileSize = struct.unpack_from("I", infile.read(4))[0]
        self.executableName = struct.unpack_from("60s", infile.read(60))[0].decode("UTF-16", errors="backslashreplace").split("\x00")[0]
        rawhash = hex(struct.unpack_from("I", infile.read(4))[0])
        self.hash = rawhash.lstrip("0x")
        unknown1 = infile.read(4)

    def fileInformation17(self, infile):
        # File Information
        # 68 bytes
        self.metricsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.metricsCount = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsCount = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsSize = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationOffset = struct.unpack_from("I", infile.read(4))[0]
        self.volumesCount = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationSize = struct.unpack_from("I", infile.read(4))[0]
        self.lastRunTime = infile.read(8)
        unknown0 = infile.read(16)
        self.runCount = struct.unpack_from("I", infile.read(4))[0]
        unknown1 = infile.read(4)

    def metricsArray17(self, infile):
        # File Metrics Array
        # 20 bytes
        unknown0 = infile.read(4)
        unknown1 = infile.read(4)
        self.filenameOffset = struct.unpack_from("I", infile.read(4))[0]
        self.filenameLength = struct.unpack_from("I", infile.read(4))[0]
        unknown2 = infile.read(4)

    def traceChainsArray17(self, infile):
        # Read through the Trace Chains Array
        # Not being parsed for information
        # Broken out as its own function for possible future use
        # 12 bytes
        infile.read(12)

    def volumeInformation17(self, infile):
        # Volume information
        # 40 bytes per entry in the array
        
        infile.seek(self.volumesInformationOffset)
        self.volumesInformationArray = []
        self.directoryStringsArray = []

        count = 0
        while count < self.volumesCount:
            self.volPathOffset = struct.unpack_from("I", infile.read(4))[0]
            self.volPathLength = struct.unpack_from("I", infile.read(4))[0]
            self.volCreationTime = struct.unpack_from("Q", infile.read(8))[0]
            self.volSerialNumber = hex(struct.unpack_from("I", infile.read(4))[0])
            self.volSerialNumber = self.volSerialNumber.rstrip("L").lstrip("0x")
            self.fileRefOffset = struct.unpack_from("I", infile.read(4))[0]
            self.fileRefSize = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsOffset = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsCount = struct.unpack_from("I", infile.read(4))[0]
            unknown0 = infile.read(4)

            self.directoryStringsArray.append(self.directoryStrings(infile))

            infile.seek(self.volumesInformationOffset + self.volPathOffset)
            volume = {}
            volume["Volume Name"] = infile.read(self.volPathLength * 2)
            volume["Creation Date"] = self.convertTimestamp(self.volCreationTime)
            volume["Serial Number"] = self.volSerialNumber
            self.volumesInformationArray.append(volume)
            
            count += 1
            infile.seek(self.volumesInformationOffset + (40 * count))

    def fileInformation23(self, infile):
        # File Information
        # 156 bytes
        self.metricsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.metricsCount = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsCount = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsSize = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationOffset = struct.unpack_from("I", infile.read(4))[0]
        self.volumesCount = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationSize = struct.unpack_from("I", infile.read(4))[0]
        unknown0 = infile.read(8)
        self.lastRunTime = infile.read(8)
        unknown1 = infile.read(16)
        self.runCount = struct.unpack_from("I", infile.read(4))[0]
        unknown2 = infile.read(84)

    def metricsArray23(self, infile):
        # File Metrics Array
        # 32 bytes per array, not parsed in this script
        infile.seek(self.metricsOffset)
        unknown0 = infile.read(4)
        unknown1 = infile.read(4)
        unknown2 = infile.read(4)
        self.filenameOffset = struct.unpack_from("I", infile.read(4))[0]
        self.filenameLength = struct.unpack_from("I", infile.read(4))[0]
        unknown3 = infile.read(4)
        self.mftSeqNumber, self.mftEntryNumber = self.convertFileReference(infile.read(8))
        #self.mftSeqNumber = struct.unpack_from("H", infile.read(2))[0]

    def volumeInformation23(self, infile):
        # This function consumes the Volume Information array
        # 104 bytes per structure in the array
        # Returns a dictionary object which holds another dictionary
        # for each volume information array entry

        infile.seek(self.volumesInformationOffset)
        self.volumesInformationArray = []
        self.directoryStringsArray = []
        
        count = 0
        while count < self.volumesCount:
            self.volPathOffset = struct.unpack_from("I", infile.read(4))[0]
            self.volPathLength = struct.unpack_from("I", infile.read(4))[0]
            self.volCreationTime = struct.unpack_from("Q", infile.read(8))[0]
            volSerialNumber = hex(struct.unpack_from("I", infile.read(4))[0])
            self.volSerialNumber = volSerialNumber.rstrip("L").lstrip("0x")
            self.fileRefOffset = struct.unpack_from("I", infile.read(4))[0]
            self.fileRefCount = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsOffset = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsCount = struct.unpack_from("I", infile.read(4))[0]
            unknown0 = infile.read(68)

            self.directoryStringsArray.append(self.directoryStrings(infile))
            
            infile.seek(self.volumesInformationOffset + self.volPathOffset)
            volume = {}
            volume["Volume Name"] = infile.read(self.volPathLength * 2)
            volume["Creation Date"] = self.convertTimestamp(self.volCreationTime)
            volume["Serial Number"] = self.volSerialNumber
            self.volumesInformationArray.append(volume)
            
            count += 1
            infile.seek(self.volumesInformationOffset + (104 * count))


    def fileInformation26(self, infile):
        # File Information
        # 224 bytes
        self.metricsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.metricsCount = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.traceChainsCount = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsOffset = struct.unpack_from("I", infile.read(4))[0]
        self.filenameStringsSize = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationOffset = struct.unpack_from("I", infile.read(4))[0]
        self.volumesCount = struct.unpack_from("I", infile.read(4))[0]
        self.volumesInformationSize = struct.unpack_from("I", infile.read(4))[0]
        unknown0 = infile.read(8)
        self.lastRunTime = infile.read(64)
        unknown1 = infile.read(16)
        self.runCount = struct.unpack_from("I", infile.read(4))[0]
        unknown2 = infile.read(96)

    def traceChainsArray30(self, infile):
        # Trace Chains Array
        # Read though, not being parsed for information
        # Broken out as its own function for possible future use
        # 8 bytes
        infile.read(8)

    def volumeInformation30(self, infile):
        # Volumes Information
        # 96 bytes

        infile.seek(self.volumesInformationOffset)
        self.volumesInformationArray = []
        self.directoryStringsArray = []

        count = 0
        while count < self.volumesCount:
            self.volPathOffset = struct.unpack_from("I", infile.read(4))[0] 
            self.volPathLength = struct.unpack_from("I", infile.read(4))[0]
            self.volCreationTime = struct.unpack_from("Q", infile.read(8))[0]
            self.volSerialNumber = hex(struct.unpack_from("I", infile.read(4))[0])
            self.volSerialNumber = self.volSerialNumber.rstrip("L").lstrip("0x")
            self.fileRefOffset = struct.unpack_from("I", infile.read(4))[0]
            self.fileRefCount = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsOffset = struct.unpack_from("I", infile.read(4))[0]
            self.dirStringsCount = struct.unpack_from("I", infile.read(4))[0]
            unknown0 = infile.read(60)

            self.directoryStringsArray.append(self.directoryStrings(infile))

            infile.seek(self.volumesInformationOffset + self.volPathOffset)
            volume = {}
            volume["Volume Name"] = infile.read(self.volPathLength * 2)
            volume["Creation Date"] = self.convertTimestamp(self.volCreationTime)
            volume["Serial Number"] = self.volSerialNumber
            self.volumesInformationArray.append(volume)
            
            count += 1
            infile.seek(self.volumesInformationOffset + (96 * count))



    def getFilenameStrings(self, infile):
        # Parses filename strings from the PF file
        infile.seek(self.filenameStringsOffset)
        self.filenames = infile.read(self.filenameStringsSize)
        self.resources = self.filenames.decode("UTF-16", errors="backslashreplace").split("\x00")[:-1]


    def convertTimestamp(self, timestamp):
        # Timestamp is a Win32 FILETIME value
        # This function returns that value in a human-readable format
        return str(datetime(1601,1,1) + timedelta(microseconds=timestamp / 10.))


    def getTimeStamps(self, lastRunTime):
        self.timestamps = []

        for timestamp in range(8):
            try:
                start_ts = timestamp * 8
                ts = struct.unpack_from("Q", lastRunTime[start_ts:start_ts + 8])[0]
                if ts:
                    self.timestamps.append(convertTimestamp(ts))
            except struct.error:
                return self.timestamps


    def directoryStrings(self, infile):
        infile.seek(self.volumesInformationOffset)
        infile.seek(self.dirStringsOffset, 1)

        directoryStrings = []

        count = 0
        while count < self.dirStringsCount:
            # Below we account for the NULL byte, which is not included in stringLength
            stringLength = struct.unpack_from("<H", infile.read(2))[0] * 2 + 2
            directoryStrings.append((infile.read(stringLength).decode("UTF-16", errors="backslashreplace")))
            count += 1
        return directoryStrings


    def convertFileReference(self, buf):
        sequenceNumber = int.from_bytes(buf[-2:], byteorder="little")
        entryNumber = int.from_bytes(buf[0:6], byteorder="little")
        return sequenceNumber, entryNumber


    def prettyPrint(self):
        # Prints important Prefetch data in a structured format
        banner = "=" * (len(ntpath.basename(self.pFileName)) + 2)
        print("\n{0}\n{1}\n{0}\n".format(banner, ntpath.basename(self.pFileName)))
        print("Executable Name: {}\n".format(self.executableName))
        print("Run count: {}\n".format(self.runCount))

        if len(self.timestamps) > 1:
            print("Last Executed:")
            for timestamp in self.timestamps:
                print("    " + timestamp)
        else:
            print("Last Executed: {}".format(self.timestamps[0]))
        
        print("\nVolume Information:")
        for i in self.volumesInformationArray:
            print("   Volume Name: " + i["Volume Name"].decode("UTF-16", errors="backslashreplace"))
            print("   Creation Date: " + i["Creation Date"])
            print("   Serial Number: " + i["Serial Number"])
            print()

        print("Directory Strings:")
        for volume in self.directoryStringsArray:
            for dirstring in enumerate(volume):
                print("{:>4}: {}".format(dirstring[0], dirstring[1]))
        print()

        print("Resources Loaded:")
        for resource in enumerate(self.resources):
            print("{:>4}: {}".format(resource[0], resource[1]))
        print()
    

def convertTimestamp(timestamp):
        # Timestamp is a Win32 FILETIME value
        # This function returns that value in a human-readable format
        return str(datetime(1601,1,1) + timedelta(microseconds=timestamp / 10.))

