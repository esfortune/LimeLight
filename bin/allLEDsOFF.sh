#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
#
# This is a simple script to capture a Studio Photo. To do this, we cycle
# the attractor and Studio LED lights. GPIO12 is Studio relay, GPIO16 is 
# attractor relay. Photo is captured using libcamera. Photos are named
# using the "datetime" option, and an entry is made in the data log.

# This is our path - set it to match config.py data_path + Studio
DIR="/home/arducam/data/curdat/Studio"


attractorOFF=6
panelOFF=13


echo "Studio lights and Attractor lights OFF"
gpioset gpiochip0 $panelOFF=1   # Set GPIO 12 to high (3.3V)
gpioset gpiochip0 $attractorOFF=1   # Set GPIO 16 to low (0V)
sleep 1
gpioset gpiochip0 $panelOFF=0   # Set GPIO 12 to high (3.3V)
gpioset gpiochip0 $attractorOFF=0   # Set GPIO 16 to low (0V)

# For the future we should be pulling the GPIO information from
# the config.py file.
