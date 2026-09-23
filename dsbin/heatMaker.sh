#!/bin/sh
# Copyright Eric Fortune, CanopyLife, September 2026
# Code written for Mothpad device.

# This is a simple script to capture a Studio Photo using 2 cameras, GPS measurement,
# and temperature.  The script cycles the attractor and Studio LED lights. 
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

timestamp=$(date +"%Y%m%d%H%M")

#########################################################################
## Check if the directory exists, make it, cd into it

if [ ! -d "$DIR" ]; then
  # Directory doesn't exist, create it
  mkdir -p "$DIR"
fi

cd $DIR

#########################################################################
# Take the pretemp

temp=`vcgencmd measure_temp | sed s/temp\=//g | sed s/\'C//g`

# Log the temp
echo $timestamp, $location", "$serialNum", PreHeatTest, NoPhoto, "$temp >> /home/canopylife/data/curdat/dataLog.csv
echo $timestamp, $location", "$serialNum", PreHeatTest, NoPhoto, "$temp 

#########################################################################
# Heat the CPU
stress-ng --cpu 0 --timeout 45

#########################################################################
# Take the posttemp

temp=`vcgencmd measure_temp | sed s/temp\=//g | sed s/\'C//g`
timestamp=$(date +"%Y%m%d%H%M")

# Log the temp
echo $timestamp, $location", "$serialNum", PostHeatTest45sec, NoPhoto, "$temp >> /home/canopylife/data/curdat/dataLog.csv
echo $timestamp, $location", "$serialNum", PostHeatTest45sec, NoPhoto, "$temp 

