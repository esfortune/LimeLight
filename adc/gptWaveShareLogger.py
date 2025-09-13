import time
import numpy as np
import struct
from ADS1263 import ADS1263

def log_ads1263_continuous(
    channel=0,
    sample_rate=10000,
    num_samples=20000,
    chunk_size=1000,
    bin_filename="samples.bin"
):
    """
    Continuous logger with chunked writes.
    Each record = (timestamp: float64, adc_value: int32)
    """
    ads = ADS1263()
    ads.ADS1263_init()
    ads.ADS1263_SetChannal(channel)

    interval = 1.0 / sample_rate
    record_size = struct.calcsize("di")  # double + int32
    buffer = bytearray(chunk_size * record_size)

    print(f"Logging {num_samples} samples at {sample_rate} Hz into {bin_filename}...")
    start_time = time.perf_counter()

    with open(bin_filename, "wb") as f:
        for i in range(num_samples):
            t = time.perf_counter()
            value = ads.ADS1263_GetChannalValue(channel)

            # pack sample into buffer
            struct.pack_into("di", buffer, (i % chunk_size) * record_size, t, value)

            # flush buffer when full
            if (i + 1) % chunk_size == 0:
                f.write(buffer)
                f.flush()

            # timing loop
            next_time = start_time + (i + 1) * interval
            while time.perf_counter() < next_time:
                pass

        # write leftover samples (if not a multiple of chunk_size)
        leftover = (num_samples % chunk_size) * record_size
        if leftover > 0:
            f.write(buffer[:leftover])
            f.flush()

    print(f"Done. File saved: {bin_filename}")

