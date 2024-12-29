#!/bin/bash

echo "Serial number: 117722760" > /home/arducam/data/Limelight_117722760_Status.txt
echo " " >> /home/arducam/data/Limelight_117722760_Status.txt
echo `date` >> /home/arducam/data/Limelight_117722760_Status.txt
echo " " >> /home/arducam/data/Limelight_117722760_Status.txt

echo "Internal NVMe: 2 Terabytes" >> /home/arducam/data/Limelight_117722760_Status.txt
echo "Raspberry Pi: Model 5, 4 Gig RAM" >> /home/arducam/data/Limelight_117722760_Status.txt
echo "Device temperature: " `vcgencmd measure_temp` >> /home/arducam/data/Limelight_117722760_Status.txt
echo " " >> /home/arducam/data/Limelight_117722760_Status.txt

echo "Total Disk Usage: " `df -h | grep T` >> /home/arducam/data/Limelight_117722760_Status.txt
echo "Current Data Collection: " `du -sh /home/arducam/data/curdat` >> /home/arducam/data/Limelight_117722760_Status.txt
echo "Backup Data: " `du -sh /home/arducam/data/backups` >> /home/arducam/data/Limelight_117722760_Status.txt
echo " " >> /home/arducam/data/Limelight_117722760_Status.txt

echo "If in Download mode but not backing up (no fast green blinking)," >> /home/arducam/data/Limelight_117722760_Status.txt
echo "reset by putting into Collection mode for about 1 minute " >> /home/arducam/data/Limelight_117722760_Status.txt
echo "and back into Download mode." >> /home/arducam/data/Limelight_117722760_Status.txt

