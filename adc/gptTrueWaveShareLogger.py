% September2025 Single channel at up to about 4kHz sample rates
% FINALLY

import time
import struct
from ADS1263 import ADS1263

channel=0
target_rate=3000         # Hz (suggest 2000 or 2500 for Pi)
num_samples=20000
chunk_size=1000
bin_filename="samples.bin"

"""
Log ADS1263 data with *true timing*.
- Reads as fast as possible, pacing toward target_rate.
- Records actual timestamp with each sample.
- Each record = (timestamp: float64, adc_value: int32).
"""

ads = ADS1263()
ads.ADS1263_init_ADC1()
ads.ADS1263_SetMode(0)
ads.ADS1263_SetChannal(channel)

interval = 1.0 / target_rate
record_size = struct.calcsize("dI")  # double + int32
buffer = bytearray(chunk_size * record_size)

print(f"Logging {num_samples} samples at ~{target_rate} Hz → {bin_filename}")
start_time = time.perf_counter()

with open(bin_filename, "wb") as f:
    for i in range(num_samples):
        t = time.perf_counter()
        value = ads.ADS1263_GetChannalValue(channel)

        struct.pack_into("dI", buffer, (i % chunk_size) * record_size, t, value)

        if (i + 1) % chunk_size == 0:
            f.write(buffer)
            f.flush()

        # Sleep only if ahead of schedule
        next_time = start_time + (i + 1) * interval
        delay = next_time - time.perf_counter()
        if delay > 0:
            time.sleep(delay)

    leftover = (num_samples % chunk_size) * record_size
    if leftover > 0:
        f.write(buffer[:leftover])
        f.flush()

print(f"Done. File saved: {bin_filename}")

