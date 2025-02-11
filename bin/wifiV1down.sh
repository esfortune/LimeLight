#!/bin/bash
# Eric Fortune, Canopy Life, February 2024
# Code written for Limelight Rainforest test device.


nmcli con down AccessPoint

sleep 1

kill -9 `head -1 /home/arducam/wifiUP.txt`

sleep 1

/home/arducam/bin/dockerDUFSkill.sh

sleep 1

rm /home/arducam/wifiUP.txt

