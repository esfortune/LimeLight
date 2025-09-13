import struct
import numpy as np
import matplotlib.pyplot as plt

def read_ads1256_binary(bin_filename="samples.bin"):
    """
    Load binary file produced by log_ads1256_binary.
    Returns numpy arrays: timestamps, values
    """
    record_size = struct.calcsize("di")  # float64 + int32
    with open(bin_filename, "rb") as f:
        data = f.read()

    num_records = len(data) // record_size
    timestamps = np.empty(num_records, dtype=np.float64)
    values = np.empty(num_records, dtype=np.int32)

    for i in range(num_records):
        t, v = struct.unpack_from("di", data, i * record_size)
        timestamps[i] = t
        values[i] = v

    return timestamps, values


def plot_ads1256_data(bin_filename="samples.bin"):
    ts, vals = read_ads1256_binary(bin_filename)
    # Normalize timestamps to start at zero
    ts -= ts[0]

    plt.figure(figsize=(10, 4))
    plt.plot(ts, vals, lw=0.8)
    plt.xlabel("Time (s)")
    plt.ylabel("ADC Value (counts)")
    plt.title(f"ADS1256 Data from {bin_filename}")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_ads1256_data("samples.bin")

