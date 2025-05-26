#!/bin/sh
# Copyright Eric Fortune, CanopyLife, April 2025 
# Code written for Mothpad device.

# This script takes an Audio Recording from a AudioMoth USB microphone.
# It also makes an entry into our logging file.
# The -d is duration in seconds. We default 60 seconds.

#########################################################################
## SET VARIABLES

# This is our data path from config.py: data_path + Audio
DIR=`grep data_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`"/Audio"

# We store the location in the first line of the /home/canopylife/location.txt file.
# We have the tr command in case the user was an idiot (like me) and had spaces or other
# special characters in there.
location=$(head -1 /home/canopylife/location.txt | tr -cd '[:alnum:]')

# Get the device serial number from /home/canopylife/serialNumber.txt
serialNum=$(head -1 /home/canopylife/serialNumber.txt | tr -cd '[:alnum:]')

yearstr=$(date +"%Y")
timestamp=$(date +"%m%d%H%M%S")

filename="${location}_${serialNum}_${yearstr}_${timestamp}.wav"
echo $filename


#########################################################################
## Make the data directory, take the Audio sample, log the recording

# Check if the directory exists
if [ ! -d "$DIR" ]; then
  # Directory doesn't exist, create it
  echo "Directory $DIR does not exist. Creating it..."
  mkdir -p "$DIR"
fi

arecord -D hw:CARD=Microphone,DEV=0 -f S16_LE -r 384000 -d 60 /home/canopylife/data/curdat/Audio/$filename

echo $location", "$serialNum", audio, "$filename", AudioMoth, S16_LE, 384000, 60" >> /home/canopylife/data/curdat/dataLog.csv
echo $location", "$serialNum", audio, "$filename", AudioMoth, S16_LE, 384000, 60" 
