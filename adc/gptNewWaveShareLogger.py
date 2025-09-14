import time
import struct
from ADS1256 import ADS1256

def log_ads1256_stable(
    channel=0,
    sample_rate=2000,          # 2000 or 2500 Hz recommended
    num_samples=20000,
    chunk_size=1000,
    bin_filename="samples.bin"
):
    """
    Stable-rate logger for ADS1256 using Python.
    Each record = (timestamp: float64, adc_value: int32).
    Uses time.sleep() pacing instead of busy-wait.
    """
    ads = ADS1256()
    ads.ADS1256_init()
    ads.ADS1256_SetChannal(channel)

    interval = 1.0 / sample_rate
    record_size = struct.calcsize("di")  # double + int32
    buffer = bytearray(chunk_size * record_size)

    print(f"Logging {num_samples} samples at {sample_rate} Hz → {bin_filename}")
    start_time = time.perf_counter()

    with open(bin_filename, "wb") as f:
        for i in range(num_samples):
            t = time.perf_counter()
            value = ads.ADS1256_GetChannalValue(channel)

            struct.pack_into("di", buffer, (i % chunk_size) * record_size, t, value)

            if (i + 1) % chunk_size == 0:
                f.write(buffer)
                f.flush()

            # Sleep until next sample time
            next_time = start_time + (i + 1) * interval
            delay = next_time - time.perf_counter()
            if delay > 0:
                time.sleep(delay)

        leftover = (num_samples % chunk_size) * record_size
        if leftover > 0:
            f.write(buffer[:leftover])
            f.flush()

    print(f"Done. File saved: {bin_filename}")

