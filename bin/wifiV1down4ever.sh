#!/bin/bash
# Eric Fortune, Canopy Life, February 2024
# Code written for Limelight Rainforest test device.

sudo nmcli con down AccessPoint

sleep 1

kill -9 `head -1 /home/arducam/wifiUP.txt`

sleep 1

/home/arducam/bin/dockerDUFSkill.sh

sleep 1

# THE USER HAS STOPPED THE WIFI, so we don't want it to restart. Until reboot.
#### rm /home/arducam/wifiUP.txt

