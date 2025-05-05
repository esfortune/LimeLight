import time
import csv
import board
import busio
import numpy as np
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# pip install adafruit-circuitpython-ads1x15
#

# Initialize I2C and ADS1015
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)
ads.data_rate = 3300  # Ensure high-speed sampling

# Select input channel (e.g., A0)
chan = AnalogIn(ads, ADS.P0)

# CSV setup
csv_filename = "ads1015_log.csv"
with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Voltage"])  # Header

    # Sampling rate control
    sample_rate = 3000  # Hz
    sample_period = 1.0 / sample_rate

    print(f"Logging data at {sample_rate} Hz... Press Ctrl+C to stop.")

    try:
        while True:
            start_time = time.perf_counter()
            voltage = chan.voltage
            timestamp = time.time()

            # Write to CSV
            writer.writerow([timestamp, voltage])

            # Maintain precise sample rate
            elapsed = time.perf_counter() - start_time
            sleep_time = sample_period - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Logging stopped.")

