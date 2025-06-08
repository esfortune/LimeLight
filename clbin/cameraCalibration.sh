#!/bin/bash
# Copyright Eric Fortune, CanopyLife, June 2025
# Code written for Mothpad device.

# This takes a series of photos for use in choosing the best focal distance.
# The photos go into the data folder, in a directory "focusTest"

# Set the directory
DIR="/home/canopylife/data/focusTest"

# Get our GPIO pins for LED latching relays from config.py
panelOFF=`grep studioOFF_gpio /home/canopylife/bin/config.py | sed 's/[^0-9]//g'`
panelON=`grep studioON_gpio /home/canopylife/bin/config.py | sed 's/[^0-9]//g'`


#########################################################################
## Check if the directory exists, make it, cd into it

if [ ! -d "$DIR" ]; then
  # Directory doesn't exist, create it
  mkdir -p "$DIR"
fi

cd $DIR

#########################################################################
## Switch Panel LED lights on for PHOTOS

gpioset gpiochip0 $panelON=1            # Set Panel On (high)
sleep 1
gpioset gpiochip0 $panelON=0            # Set Panel On (low)

# Sleep 2 seconds to ensure that the lights are stable
sleep 2

#########################################################################

for pos in $(seq 6.8 0.1 7.8); do

filenam=`echo $pos | sed 's/[^0-9]*//g'`

  echo "Capturing with lens-position: $pos"
#  libcamera-still -n --datetime --autofocus-mode manual --lens-position "$pos" --sharpness 2 --exposure sport
  libcamera-still -n --autofocus-mode manual --lens-position "$pos" --sharpness 2 --exposure sport -o $filenam.jpg
  sleep 1

  filename=`ls -t *.jpg | head -1`

  convert $filename -gravity North -pointsize 256 -fill red -annotate +0+30 "Lens Position $pos" tmp.jpg
  mv tmp.jpg $filename

done

#########################################################################
## Switch Panel LED lights off

gpioset gpiochip0 $panelOFF=1            # Set GPIO 12 to low (0V)
sleep 1
gpioset gpiochip0 $panelOFF=0            # Set GPIO 12 to low (0V)

