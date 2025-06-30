#!/bin/bash
# Copyright Eric Fortune, CanopyLife, June 2025
# Code written for Mothpad device.

#########################################################################
## SET VARIABLES

datestamp=$(date +"%Y%b%d")

dataDIR=`grep data_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`

# This is our backup path from config.py with the current date
backupDIR=`grep backup_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`/$datestamp

echo $dataDIR $backupDIR

if [ -d "$dataDIR" ]; then
   # Directory the data directory exists, we can move forward

   if [ ! -d "$backupDIR" ]; then
      # If backup directory doesn't exist, then make it
      mkdir -p "$backupDIR"
   fi

   mv $dataDIR/* $backupDIR

fi

## Check to see the position of the switch. If it is 1, then we are in "standard" mode
## and we should make the timelapse movie.

/home/canopylife/bin/checkMode.py
status=$?

if [ $status = 1 ]; then

   # Make the movie
   /home/canopylife/bin/movieMaker.sh $backupDIR

fi
