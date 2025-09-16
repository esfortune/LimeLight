#!/usr/bin/env python3
import struct
import csv
import sys
import os

# Adjust this if you change number of channels in the logger
NUM_CHANNELS = 4

def bin_to_csv(bin_filename):
    csv_filename = os.path.splitext(bin_filename)[0] + ".csv"

    record_size = struct.calcsize("d" + "i" * NUM_CHANNELS)

    with open(bin_filename, "rb") as fbin, open(csv_filename, "w", newline="") as fcsv:
        writer = csv.writer(fcsv)
        # header
        writer.writerow(["timestamp"] + [f"ch{ch}" for ch in range(NUM_CHANNELS)])

        while True:
            chunk = fbin.read(record_size)
            if not chunk:
                break
            record = struct.unpack("d" + "i" * NUM_CHANNELS, chunk)
            writer.writerow(record)

    print(f"Converted {bin_filename} → {csv_filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} samples.bin")
        sys.exit(1)

    bin_to_csv(sys.argv[1])

