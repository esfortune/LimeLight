#!/home/arducam/eINK/bin/python3
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
# Update the system status on the eINK display.
# 
adapim = 1 # use 1 if Adafruit 1675, use 9 if Pimoroni 1608

import time
import board
import busio
import shutil
import subprocess
from digitalio import DigitalInOut
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from PIL import Image, ImageDraw, ImageFont

import config as c

# SPI bus and display pin setup
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs_pin = DigitalInOut(board.D25)  # Chip select D25
dc_pin = DigitalInOut(board.D22)   # Data/command D24 new D22
rst_pin = DigitalInOut(board.D27)  # Reset D17 new D27
busy_pin = DigitalInOut(board.D17)  # Busy D4 new D17

statusLED = c.statusLED

deviceSerial = "SN: " + c.deviceSerial
timestamp = time.strftime('%d%b%Y-%H:%M:%S')
diskTotal, diskUsed, diskFree = shutil.disk_usage("/")
diskUsage = str(round(diskTotal / (1024**3))) + "Gb, " + str(round(diskUsed / (1024**3))) + "Gb, " + str(round(diskFree / (1024**3))) + "Gb"
diskPerCentRemaining = "Percent Free:  " + str(round((diskFree / diskTotal) * 100)) + " %"

currentMode = subprocess.run([c.checkMode], capture_output=True, text=True)
if currentMode.returncode == 1:
    modeMSG = "Switch: Collection Mode"
if currentMode.returncode == 0:
    modeMSG = "Switch: Download Mode"

# Initialize display
display = Adafruit_SSD1675(250, 122, spi, cs_pin=ecs_pin, dc_pin=dc_pin, sramcs_pin=None,
                           rst_pin=rst_pin, busy_pin=busy_pin)

# Clear display and set rotation (optional)
display.rotation = 2
display.fill(Adafruit_EPD.WHITE)  # Clear to white

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)
display.rotation = 0

image = Image.new("L", (display.width, display.height), 255)  # White background
draw = ImageDraw.Draw(image)

draw.text((adapim, 1), deviceSerial, font=font, fill=0)
draw.text((adapim, 15), timestamp, font=font, fill=0)
draw.text((adapim, 40), "Total, Used, Free", font=font, fill=1)
draw.text((adapim, 50), diskUsage, font=font, fill=0)
draw.text((adapim, 65), diskPerCentRemaining, font=font, fill=0)
draw.text((adapim, 90), modeMSG, font=font, fill=0)

display.image(image)
display.display() 

time.sleep(1)
ledBlink = subprocess.Popen([statusLED, '6'])

print(f"{deviceSerial}, {timestamp}, {diskUsage}, {diskPerCentRemaining}")
