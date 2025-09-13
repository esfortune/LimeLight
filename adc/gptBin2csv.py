import struct
import csv
import os

def bin_to_csv(bin_filename="samples.bin", csv_filename="samples.csv"):
    record_size = struct.calcsize("di")  # float64 + int32
    file_size = os.path.getsize(bin_filename)
    num_records = file_size // record_size

    with open(bin_filename, "rb") as fbin, open(csv_filename, "w", newline="") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["timestamp", "value"])  # header

        for _ in range(num_records):
            record = fbin.read(record_size)
            t, v = struct.unpack("di", record)
            writer.writerow([t, v])

    print(f"Converted {num_records} samples to {csv_filename}")

if __name__ == "__main__":
    bin_to_csv("samples.bin", "samples.csv")

