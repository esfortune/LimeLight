#!/bin/bash

# These are our paths - set them to match config.py data_path and backup path
CURDIR="/home/arducam/data/curdat"
BAKDIR="/home/arducam/data/backups"


# Check if the curdat directory exists
if [ ! -d "$CURDIR" ]; then
  # Directory doesn't exist, create it
  echo "Directory $CURDIR does not exist. Creating it..."
  mkdir -p "$CURDIR"
fi

# Check if the backups directory exists
if [ ! -d "$BAKDIR" ]; then
  # Directory doesn't exist, create it
  echo "Directory $BAKDIR does not exist. Creating it..."
  mkdir -p "$BAKDIR"
fi

echo "Serial number: 117608014" > /home/arducam/data/Limelight_117608014_Status.txt
echo " " >> /home/arducam/data/Limelight_117608014_Status.txt
echo `date` >> /home/arducam/data/Limelight_117608014_Status.txt
echo " " >> /home/arducam/data/Limelight_117608014_Status.txt

echo "Internal NVMe: 2 Terabytes" >> /home/arducam/data/Limelight_117608014_Status.txt
echo "Raspberry Pi: Model 5, 4 Gig RAM" >> /home/arducam/data/Limelight_117608014_Status.txt
echo "Device temperature: " `vcgencmd measure_temp` >> /home/arducam/data/Limelight_117608014_Status.txt
echo " " >> /home/arducam/data/Limelight_117608014_Status.txt

echo "Total Disk Usage: " `df -h | grep T` >> /home/arducam/data/Limelight_117608014_Status.txt
echo "Current Data Collection: " `du -sh /home/arducam/data/curdat` >> /home/arducam/data/Limelight_117608014_Status.txt
echo "Backup Data: " `du -sh /home/arducam/data/backups` >> /home/arducam/data/Limelight_117608014_Status.txt
echo " " >> /home/arducam/data/Limelight_117608014_Status.txt

echo "If in Download mode but not backing up (no fast green blinking)," >> /home/arducam/data/Limelight_117608014_Status.txt
echo "reset by putting into Collection mode for about 1 minute " >> /home/arducam/data/Limelight_117608014_Status.txt
echo "and back into Download mode." >> /home/arducam/data/Limelight_117608014_Status.txt

