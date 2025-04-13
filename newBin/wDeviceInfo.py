#!/home/arducam/eINK/bin/python3
# Eric Fortune, Canopy Life, April 2025
# Code written for MothPad device.
# Update the system status for web user
# 

import time
import shutil
import subprocess

import config as c

statusLED = c.statusLED

deviceSerial = "SN: " + c.deviceSerial
deviceLocation = "Location: " + c.deviceLocation
deviceGPS = "GPS: " + c.deviceGPS + "\n"

timestamp = time.strftime('%d%b%Y-%H:%M:%S')
printTime = "Device Time: " + timestamp + "\n"

diskTotal, diskUsed, diskFree = shutil.disk_usage("/")

diskUsage = str(round(diskTotal / (1024**3))) + "Gb space - " + str(round(diskUsed / (1024**3))) + "Gb used = " + str(round(diskFree / (1024**3))) + "Gb available."

diskPerCentRemaining = "Percent Free: " + str(round((diskFree / diskTotal) * 100)) + "%"

currentMode = subprocess.run([c.checkMode], capture_output=True, text=True)
if currentMode.returncode == 1:
    modeMSG = "Normal Mode"
if currentMode.returncode == 0:
    modeMSG = "LowPower Mode"

ledBlink = subprocess.Popen([statusLED, '2'])

print(f"{deviceSerial}, {deviceLocation}, {deviceGPS}")
print(f"{printTime}")
print(f"{diskUsage} {diskPerCentRemaining}")

time.sleep(2)

ledBlink.kill()
ledBlink = subprocess.Popen([statusLED, '6'])

