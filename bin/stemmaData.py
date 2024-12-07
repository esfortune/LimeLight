#!/home/arducam/Stemma/bin/python3
# This script reads data from our Stemma devices and
# saves to a CSV file

import time
import board
import csv
import adafruit_mpu6050 # Gyroscope
import adafruit_bme680  # Environmental sensor

import config as c

csv_file = c.stemma_csvfile

# Our Stemma boards
i2c = board.I2C()  # uses board.SCL and board.SDA
mpu = adafruit_mpu6050.MPU6050(i2c)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

# Time and Date
datestamp = time.strftime('%Y-%m-%d')
timestamp = time.strftime('%H:%M:%S')

# Get the data (no error handling at the moment)

# MPU6050
Acc = mpu.acceleration
Gyro = mpu.gyro
Temp = mpu.temperature

# BME688
gas = bme680.gas
hum = bme680.relative_humidity
pres = bme680.pressure
alti = bme680.altitude

# CSV logging

# Generate header if the file does not exist
try:
    with open(csv_file, mode='r') as file:
        print()
except FileNotFoundError:
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header to CSV file if it's new
        writer.writerow(['Date', 'Time', 'AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ', 'Temp', 'Gas', 'Humidity', 'Pressure', 'Altitude'])

# Append the data
with open(csv_file, mode='a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([datestamp, timestamp, Acc[0], Acc[1], Acc[2], Gyro[0], Gyro[1], Gyro[2], Temp, gas, hum, pres, alti])

