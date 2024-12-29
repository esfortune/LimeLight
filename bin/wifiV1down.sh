#!/bin/bash

nmcli con down AccessPoint

rm /home/arducam/wifiUP.txt

sleep 1

/home/arducam/bin/dockerDUFSkill.sh

