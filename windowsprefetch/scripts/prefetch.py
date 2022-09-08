import os
import sys
from argparse import ArgumentParser
from windowsprefetch import Prefetch


# Note: This wrapper script is a work in progress, and needs to be refined.
# todo: robust error handling and notifications, built into result output.
# todo: error-handling based on file content, not just file extension


def main():
    p = ArgumentParser()
    p.add_argument("-c", "--csv", help="Present results in CSV format", action="store_true")
    p.add_argument("-f", "--file", help="Parse a given Prefetch file", required=True)
    args = p.parse_args()


    file_paths = []
    if os.path.isdir(args.file):
        for filename in os.listdir(args.file):
            file_paths.append(os.path.join(args.file, filename))
    else:
        file_paths.append(args.file)


    parsed_files = []
    for filepath in file_paths:
        if filepath.endswith(".pf"):
            if os.path.getsize(filepath) > 0:
                p = Prefetch(filepath)
                parsed_files.append(p)

    if args.csv:
        print("Timestamp,Executable Name,Prefetch Hash,MFT Seq Number,MFT Entry Number,Run Count")

    for p in parsed_files:
        if args.csv:
            if p.version > 17:
                for timestamp in p.timestamps:
                    print("{},{},{},{},{},{}".format(
                        timestamp,
                        p.executableName,
                        p.hash,                        
                        p.mftSeqNumber,
                        p.mftEntryNumber,
                        p.runCount
                    ))
            else:
                for timestamp in p.timestamps:
                    print("{},{},{},{},{},{}".format(
                        timestamp,
                        p.executableName,
                        p.hash,
                        "N/A",
                        "N/A",
                        p.runCount
                    ))
        else:
            p.prettyPrint()


if __name__ == '__main__':
    main()
