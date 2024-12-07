#!/bin/sh
# This is a simple script to capture a Studio Photo. To do this, we cycle
# the attractor and Studio LED lights. GPIO12 is Studio relay, GPIO16 is 
# attractor relay. Photo is captured using libcamera. Photos are named
# using the "datetime" option, and an entry is made in the data log.

# This is our path - set it to match config.py data_path + Studio
DIR="/home/arducam/data/curdat/Studio"

# Check if the directory exists
if [ ! -d "$DIR" ]; then
  # Directory doesn't exist, create it
  echo "Directory $DIR does not exist. Creating it..."
  mkdir -p "$DIR"
fi

cd $DIR

attractorON=16
attractorOFF=13
panelON=12
panelOFF=6


# Turn off attractor and turn on Studio lights

echo "Turning Studio lights ON and Attractor OFF"
gpioset gpiochip0 $panelON=1   # Set GPIO 12 to high (3.3V)
gpioset gpiochip0 $attractorOFF=1   # Set GPIO 16 to low (0V)
sleep 1
gpioset gpiochip0 $panelON=0   # Set GPIO 12 to high (3.3V)
gpioset gpiochip0 $attractorOFF=0   # Set GPIO 16 to low (0V)

# Sleep 4 seconds to ensure that the lights are stable
sleep 4
# Capture the photo
libcamera-still -n --datetime

# Log the capture
filename=`ls -t *.jpg | head -1`
echo "studio, "$filename", OwlSight, 4624x3472" >> /home/arducam/data/curdat/dataLog.csv

# Sleep 2 second to ensure that everything is completed before switching.

echo "Turning Studio lights OFF and Attractor ON"
gpioset gpiochip0 $attractorON=1   # Set GPIO 16 to high (3.3V)
gpioset gpiochip0 $panelOFF=1   # Set GPIO 12 to low (0V)
sleep 1
gpioset gpiochip0 $attractorON=0   # Set GPIO 16 to high (3.3V)
gpioset gpiochip0 $panelOFF=0   # Set GPIO 12 to low (0V)

