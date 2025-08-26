#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for MothPad device.
#
# This is a simple script to turn off the attractor and Studio LEDs.
# Extract the GPIO pin numbers from config.py

studioON=`grep studioON_gpio /home/canopylife/bin/config.py | sed 's/[^0-9]//g'`

# Pull up the GPIO pin to trigger the locking relay, then turn it off.
# The pulse is 1 second in duration - we use the sleep command.

gpioset gpiochip0 $studioON=1         # Set GPIO high
sleep 1
gpioset gpiochip0 $studioON=0         # Set GPIO to low

timestamp=$(date +"%Y%m%d%H%M%S")
echo $timestamp", Studio LEDs ON"


