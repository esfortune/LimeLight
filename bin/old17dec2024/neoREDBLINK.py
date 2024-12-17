#!/home/arducam/neopixel/bin/python3
#
# requires adafruit-circuitpython-neopixel-spi
# Setup in virtual environment
# python3 -m venv neopixel
# cd neopixel
# bin/pip3 install adafruit-circuitpython-neopixel-spi

# Import libraries
import time
import board
import neopixel_spi 

# RPi version in 2024 needs SPI.  Hopefully this will be fixed soon.
pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), 10)

Xn = 1 # Number of times to blink

print(f'Displaying RED blinks')
# Display blink Xn times Red at 2 Hz
count = 0
while count < Xn:
    pixels.fill(0xff0000)
    pixels.fill(0xff0000)
    time.sleep(0.5)
    pixels.fill(0x000000)
    pixels.fill(0x000000)
    time.sleep(0.5)
    count += 1

time.sleep(0.1)

# Ensure that the LED is off
pixels.fill(0x000000)
pixels.fill(0x000000)

