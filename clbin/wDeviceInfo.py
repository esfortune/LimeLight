#!/home/canopylife/PyEnvs/neopixel/bin/python3
# Eric Fortune, Canopy Life, March 2026
# Code written for MothPad device.
# Update the system status for web user
# 

import time
import shutil
import subprocess

import config as c

# statusLED = c.statusLED # Hidden until I'm sure about what to do with the indicator LED

deviceSerial = "SN: " + c.deviceSerial
deviceLocation = "Location: " + c.deviceLocation
deviceGPS = "GPS: " + c.deviceGPS + "\n"

timestamp = time.strftime('%d%b%Y-%H:%M:%S')
printTime = "Device Time: " + timestamp + "\n"

diskTotal, diskUsed, diskFree = shutil.disk_usage("/")

diskUsage = str(round(diskTotal / (1024**3))) + "Gb, " + str(round(diskUsed / (1024**3))) + "Gb, " + str(round(diskFree / (1024**3))) + "Gb"

diskPerCentRemaining = "Percent Free:  " + str(round((diskFree / diskTotal) * 100)) + " %"

tzResult = subprocess.run(["cat", "/etc/timezone"], capture_output=True, text=True)
timeZone = "Time Zone: " + tzResult.stdout.strip()

currentMode = subprocess.run([c.checkMode], capture_output=True, text=True)
if currentMode.returncode == 1:
    modeMSG = "Normal Mode"
if currentMode.returncode == 0:
    modeMSG = "LowPower Mode"

# ledBlink = subprocess.Popen([statusLED, '2'])

print(f"{deviceSerial}, {deviceLocation}, {deviceGPS}")
print(f"{printTime}, {timeZone}")
print(f"{diskUsage}, {diskPerCentRemaining}")

# time.sleep(5)

# ledBlink.kill()
# ledBlink = subprocess.Popen([statusLED, '6'])
