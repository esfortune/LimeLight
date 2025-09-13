import time
import numpy as np
import struct
from ADS1256 import ADS1256

def log_ads1256_binary(channel=0, sample_rate=10000, num_samples=20000, bin_filename="samples.bin"):
    """
    High-speed logger: collect data at ~10kHz and store in binary file.
    Format: each record = (timestamp: float64, adc_value: int32)
    """
    ads = ADS1256()
    ads.ADS1256_init()
    ads.ADS1256_SetChannal(channel)

    interval = 1.0 / sample_rate
    record_size = struct.calcsize("di")  # double + int32
    buffer = bytearray(num_samples * record_size)

    print(f"Logging {num_samples} samples at {sample_rate} Hz to {bin_filename}...")
    start_time = time.perf_counter()

    for i in range(num_samples):
        t = time.perf_counter()
        value = ads.ADS1256_GetChannalValue(channel)
        struct.pack_into("di", buffer, i * record_size, t, value)

        next_time = start_time + (i + 1) * interval
        while time.perf_counter() < next_time:
            pass  # busy wait

    with open(bin_filename, "wb") as f:
        f.write(buffer)

    print(f"Done. File saved: {bin_filename} ({len(buffer)} bytes)")

