import time
import csv
import board
import busio
import numpy as np
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C and ADS1015
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)
# ads.data_rate = 3300  # Set high-speed sampling
ads.mode = 0

# Select input channel (e.g., A0)
chan = AnalogIn(ads, ADS.P0)

# CSV setup
csv_filename = "ads1015_log.csv"
buffer_size = 100  # Buffer 4000 samples before writing
data_buffer = np.zeros((buffer_size, 2))  # Preallocate NumPy array for timestamp and voltage

sample_rate = 3000  # Hz
sample_period = 1.0 / sample_rate
buffer_index = 0  # Buffer position tracker

print(f"Logging data at {sample_rate} Hz... Press Ctrl+C to stop.")

with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Voltage"])  # CSV Header

    try:
        while True:
            # start_time = time.perf_counter()

            # Read ADC and store in buffer
            data_buffer[buffer_index, 0] = time.time()  # Timestamp
            # data_buffer[buffer_index, 0] = sample_rate  # Timestamp
            data_buffer[buffer_index, 1] = chan.voltage  # Voltage
            buffer_index += 1

            # Write buffer to file in chunks
            if buffer_index >= buffer_size:
                writer.writerows(data_buffer)
                buffer_index = 0  # Reset buffer index

            # Maintain precise sample rate
            # elapsed = time.perf_counter() - start_time
            # sleep_time = sample_period - elapsed
            # if sleep_time > 0:
            #     time.sleep(sleep_time)

    except KeyboardInterrupt:
        # Write remaining data before exiting
        if buffer_index > 0:
            writer.writerows(data_buffer[:buffer_index])
        print("Logging stopped.")

