#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.

# This is a simple script to run SUDO to mount the portable drive.
# An appropriate fstab entry is required. Here is an example:
# /dev/sda1 /mnt/usb exfat defaults,noauto,uid=1000,gid=1000,dmask=000,fmask=111 0 0

mount /mnt/usb
