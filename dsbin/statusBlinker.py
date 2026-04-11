#!/home/canopylife/PyEnvs/neopixel/bin/python3
# Copyright Eric Fortune, CanopyLife, March 2026
# Code written for MothPad device.

# This produces different patterns of blinking from an
# Adafruit DotStar 5050 RGB LED via SPI.

import sys
from time import sleep
import board
import adafruit_dotstar as dotstar

try:
    pixels = dotstar.DotStar(board.SCK, board.MOSI, 1, brightness=1.0, pixel_order=dotstar.RGB)
except AttributeError:
    pixels = dotstar.DotStar(board.SCLK, board.MOSI, 1, brightness=1.0, pixel_order=dotstar.RGB)

def blinking_slowPURPLE(): # A slower purple blinking that asks the user to intervene
    while True:
        pixels.fill(0xffff00) # Color Purple
        sleep(0.2)  # 200ms on
        pixels.fill(0x000000)
        sleep(1.00)  # 1 second off

def blinking_fastGREEN(): # Fast green blinking as if machine is working
    while True:
        pixels.fill(0x000080) # Color Green
        #pixels.fill(0x008000)
        sleep(0.15)
        pixels.fill(0x000000)
        sleep(0.15)

def blinking_fastRED(): # Fast red blinking for 60 seconds then exits cleanly
    import time
    end_time = time.time() + 60
    while time.time() < end_time:
        pixels.fill(0xff0000) # Color Red
        sleep(0.15)
        pixels.fill(0x000000)
        sleep(0.15)
    pixels.fill(0x000000)
    sleep(0.1)
    pixels.fill(0x000000)

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

def blink_fourRED(): # Four long red blinks to tell you to reset
    jj = 0
    while jj < 4:
        pixels.fill(0xff0000)
        sleep(1)
        pixels.fill(0x000000)
        sleep(1)
        jj += 1

def blink_fourBLUE(): # Four long blue blinks to tell you all is OK
    jj = 0
    while jj < 4:
        pixels.fill(0x008000) # Color Blue
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
        blinking_slowPURPLE()
    elif sys.argv[1] == '2':
        blinking_fastGREEN()
    elif sys.argv[1] == '3':
        blinking_fastRED()
    elif sys.argv[1] == '4':
        blink_fourBLUE()
    elif sys.argv[1] == '5':
        blink_fourRED()
    elif sys.argv[1] == '6':
        blink_OFF()

if __name__ == "__main__":
    main()

