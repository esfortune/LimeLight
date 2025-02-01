#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.

# This is a trivial GPS reader for RPi5 with Adafruit Ultimate GPS hat. This should
# work with any setup, but may need to change the dev to serial0 or ttyAMA10.
# The 20 lines from the head command is arbitrary - it seems to work well enough.
# The timeout is to prevent a hang in case no data is being sent to the serial port.
# This happens if there is no GPS device attached, or the GPS device has died.

# Set path to match config.py: data_path 
timeout 10 head -20 /dev/ttyAMA0 | strings | grep RMC | tail -1 >> /home/arducam/data/curdat/gpsData.csv

