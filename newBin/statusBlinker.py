#!/home/arducam/neopixel/bin/python3
# Copyright Eric Fortune, CanopyLife, April 2025 
# Code written for MothPad device.

# This produces different patterns of blinking from an
# Adafruit Neopixel multicolor LED.

import sys
from time import sleep
import board
import neopixel_spi

# RPi version in 2025 needs SPI.  Hopefully this will be fixed soon.
pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), 10)

### Custom
import config as c

def blinking_slowPURPLE(): # A slower purple blinking that asks the user to intervene
    while True:
        pixels.fill(0x800080)
        sleep(0.02)  # 20Hz -> 0.020 seconds on
        pixels.fill(0x000000)
        sleep(1.00)  # 20Hz -> 0.480 seconds off

def blinking_fastGREEN(): # Fast green blinking as if machine is working
    while True:
        pixels.fill(0x008000)
        sleep(0.05)
        pixels.fill(0x000000)
        sleep(0.05)

def blinking_fastRED(): # Fast green blinking as if machine is working
    while True:
        pixels.fill(0xff0000)
        sleep(0.05)
        pixels.fill(0x000000)
        sleep(0.05)

def blinking_doubletsRED(): # Double red blink that is definitely an error
    while True:
        pixels.fill(0xff0000)
        sleep(0.2)
        pixels.fill(0x000000)
        sleep(0.1)
        pixels.fill(0xff0000)
        sleep(0.2)
        pixels.fill(0x000000)
        sleep(1.6)

def blink_fourRED(): # This is four long red blinks to tell you to reset
    jj = 0
    while jj < 4:
        pixels.fill(0xff0000)
        sleep(1)
        pixels.fill(0x000000)
        sleep(1)
        jj += 1

def blink_fourGREEN(): # This is two long green blinks to tell you all is OK
    jj = 0
    while jj < 4:
        pixels.fill(0x008000)
        sleep(1)
        pixels.fill(0x000000)
        sleep(1)
        jj += 1

def blink_OFF(): # Ensure that the LED has been turned off
    pixels.fill(0x000000)
    sleep(0.1)
    pixels.fill(0x000000)

def main():
    # Check if the argument is passed and valid
    if len(sys.argv) != 2 or sys.argv[1] not in ['1', '2', '3', '4', '5', '6']:
        print("Usage: python3 statusBlinker.py <1|6>: 1-Purple, 2-Green, 3-Red, 4-Greens, 5-Reds, 6-Off")
        sys.exit(1)
    
    # Determine the blink pattern based on the argument
    if sys.argv[1] == '1':
        blinking_fastRED()
    elif sys.argv[1] == '2':
        blinking_fastGREEN() 
    elif sys.argv[1] == '3':
        blinking_doubletsRED()
    elif sys.argv[1] == '4':
        blink_fourGREEN()
    elif sys.argv[1] == '5':
        blink_fourRED()
    elif sys.argv[1] == '6':
        blink_OFF()

if __name__ == "__main__":
    main()

