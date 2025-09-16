import time
import struct
from ADS1263 import ADS1263

channels = [0, 1, 2, 3]   # four channels
target_rate = 2000        # Hz (samples per group of 4)
num_samples = 20000
chunk_size = 1000
bin_filename = "samples.bin"

"""
Log ADS1263 data with *true timing*.
- Uses ADS1263_GetAll() to poll all enabled channels at once.
- Records actual timestamp once per group.
- Each record = (timestamp: float64, ch0: int32, ch1: int32, ch2: int32, ch3: int32).
"""

ads = ADS1263()
ads.ADS1263_init_ADC1()
ads.ADS1263_SetMode(0)

# Enable all four channels at once (bitmask)
channel_mask = 0
for ch in channels:
    channel_mask |= (1 << ch)
ads.ADS1263_SetChannal(channel_mask)

interval = 1.0 / target_rate
record_size = struct.calcsize("d" + "i" * len(channels))  # double + N*int32
buffer = bytearray(chunk_size * record_size)

print(f"Logging {num_samples} samples of {len(channels)} channels at ~{target_rate} Hz → {bin_filename}")
start_time = time.perf_counter()

with open(bin_filename, "wb") as f:
    for i in range(num_samples):
        t = time.perf_counter()

        # Poll all enabled channels simultaneously
        values = ads.ADS1263_GetAll()[:len(channels)]

        # Pack timestamp + all channel values
        struct.pack_into(
            "d" + "i" * len(channels),
            buffer,
            (i % chunk_size) * record_size,
            t,
            *values
        )

        # Write in chunks
        if (i + 1) % chunk_size == 0:
            f.write(buffer)
            f.flush()

        # pacing
        next_time = start_time + (i + 1) * interval
        delay = next_time - time.perf_counter()
        if delay > 0:
            time.sleep(delay)

    # flush remainder
    leftover = (num_samples % chunk_size) * record_size
    if leftover > 0:
        f.write(buffer[:leftover])
        f.flush()

print(f"Done. File saved: {bin_filename}")

