#!/usr/bin/python
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
#
# This checks the disk space. If there is less than 100 Mb free, shut the
# device down. Otherwise repore the disk space to STDOUT.

import psutil
import os
import time

# Set the threshold for free space (in bytes)
threshold = 100 * 1024 * 1024  # 100 MB in bytes

disk_usage = psutil.disk_usage('/')

# Check if free space is greater than or equal to the threshold
if disk_usage.free <= threshold:
    print(f"100 MB or less of free space is available: {disk_usage.free / (1024 * 1024):.2f} MB")
    os.system("timeout 5 statusBlinker.py 3")
    os.system("eINKdiskfullmsg.py")
    os.system("sudo shutdown -h now")

else:
    print(f"Current disk usage: {disk_usage.free / (1024 * 1024) /  1000:.2f} GB")
        
