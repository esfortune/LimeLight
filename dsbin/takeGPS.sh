#!/bin/sh
# Eric Fortune, Canopy Life, July 2025 
# Code written for Limelight Rainforest test device.

# This is a trivial GPS reader for RPi5 for either GooUU Tech GT-U7 or Adafruit
# Ultimate GPS hat. This should work with any setup, but may need to change the
# dev to serial0 or tty.  The 20 lines from the head command is arbitrary
# - it seems to work well enough.  The timeout is to prevent a hang in case no
# data is being sent to the port.  This happens if there is no GPS device
# attached, or the GPS device has died.

# Set path to match config.py: data_path 

# Adafruit Ultimate GPS Hat
# timeout 10 head -20 /dev/ttyAMA0 | strings | grep RMC | tail -1 >> /home/canopylife/data/curdat/gpsData.csv

# U-Blox AG [u-blox 7] Goouuu Tech GT-07
timeout 10 head -20 /dev/ttyACM0 | strings | grep RMC | tail -1 >> /home/canopylife/data/curdat/gpsData.csv
