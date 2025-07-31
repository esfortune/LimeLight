#!/bin/sh
# Copyright Eric Fortune, CanopyLife, April 2025
# Code written for Mothpad device.

# This is a simple script to capture a Studio Photo. To do this, we cycle
# the attractor and Studio LED lights. 
# Photo is captured using rpicam. Photos are named
# using the "datetime" option, and an entry is made in the data log.
# Relies on location + serialNumber files and config.py


#########################################################################
## SET VARIABLES

# This is our data path from config.py: data_path + Studio
DIR=`grep data_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`"/Studio"

# We store the location in the first line of the /home/canopylife/location.txt file.
# We have the tr command in case the user was an idiot (like me) and had spaces or other
# special characters in there.
location=$(head -1 /home/canopylife/location.txt | tr -cd '[:alnum:]')

# Get the device serial number from /home/canopylife/serialNumber.txt
serialNum=$(head -1 /home/canopylife/serialNumber.txt | tr -cd '[:alnum:]')

yearstr=$(date +"%Y")

# Get our GPIO pins for LED lcatching relays from config.py
attractorOFF=`grep attractorOFF_gpio /home/canopylife/bin/config.py | sed 's/[^0-9]//g'`
attractorON=`grep attractorON_gpio /home/canopylife/bin/config.py | sed 's/[^0-9]//g'`
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
## Switch LED lights for PHOTO

gpioset gpiochip0 $panelON=1            # Set Panel On (high)
gpioset gpiochip0 $attractorOFF=1       # Set Attractor Off (high)
sleep 1
gpioset gpiochip0 $panelON=0            # Set Panel On (low)
gpioset gpiochip0 $attractorOFF=0       # Set Attractor (low)

# Sleep 3 seconds to ensure that the lights are stable
sleep 3

#########################################################################
# Capture the photo

# rpicam-still -n --datetime --autofocus-range macro 
rpicam-still -n --datetime --autofocus-mode manual --lens-position 7 --sharpness 2 --exposure sport
filename=`ls -t *.jpg | head -1`

sleep 1

# Rename the file
mv "$filename" "${location}_${serialNum}_${yearstr}_${filename}"

# Log the photo
newFilename=`ls -t *.jpg | head -1`
echo $location", "$serialNum", Studio, "$newFilename", OwlSight, 4624x3472" >> /home/canopylife/data/curdat/dataLog.csv
echo $location", "$serialNum", Studio, "$newFilename", OwlSight, 4624x3472" 

#########################################################################
## Switch LED lights for ATTRACTION

gpioset gpiochip0 $attractorON=1         # Set GPIO 16 to high (3.3V)
gpioset gpiochip0 $panelOFF=1            # Set GPIO 12 to low (0V)
sleep 1
gpioset gpiochip0 $attractorON=0         # Set GPIO 16 to high (3.3V)
gpioset gpiochip0 $panelOFF=0            # Set GPIO 12 to low (0V)

