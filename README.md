# LimeLight
Limelight development, Updated 7-October-2024

This is code to run on an RPi•5 Limelight controller. 
This includes code for data aquisition and management.
Data currently include the Insect studio, MicroMoth USB Audio, and GPS.
Plan to add basic environmental data (temperature, humidity, etc.)

Uses a combination of Python and shell (/bin/sh) scripts controlled by crontab.

# Hardward details

Ultimate GPS Hat (Adafruit)
AudioMoth USB Microphone (384kHz sample rate)
Arducam Owlsight camera (64MP)
"Acquisition / Download" DPDT switch @ GPIO23
Studio Illumination GPIO12 (latching relay)
Attractor Illumination GPIO16 (latching relay)

# Code details

Code in /home/arducam/bin
Data in /home/arducam/data
Backups in /home/arducam/backup
USB mount /mnt/usb (see fstab)

# USAGE

Indicator LEDs (Power, Switch, Status via NEOPIXEL)

