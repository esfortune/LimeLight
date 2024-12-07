#!/home/arducam/eINK/bin/python3

import time
import board
import busio
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

# Initialize display
display = Adafruit_SSD1675(250, 122, spi, cs_pin=ecs_pin, dc_pin=dc_pin, sramcs_pin=None,
                           rst_pin=rst_pin, busy_pin=busy_pin)

# Clear display and set rotation (optional)
display.rotation = 1
display.fill(Adafruit_EPD.WHITE)  # Clear to white


# Load a font (optional, you can use a system font or provide your own)
# try:
#     font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
# except IOError:
#     font = ImageFont.load_default()


#font = ImageFont.load_default()
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
textL1 = "NextGen Limelight"
textL2 = "XPRIZE winners!"
display.rotation = 1


image = Image.new("L", (display.width, display.height), 255)  # White background
draw = ImageDraw.Draw(image)

draw.text((1, 30), textL1, font=font, fill=0)
draw.text((1, 80), textL2, font=font, fill=0)

display.image(image)
display.display() 

time.sleep(1)
ledBlink = subprocess.Popen([statusLED, '6'])

