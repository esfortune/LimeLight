#!/bin/bash
# Version 1 from https://forums.raspberrypi.com/viewtopic.php?t=357998
# Eric Fortune, Canopy Life, February 2024
# Code written for Limelight Rainforest test device.

nmcli con delete AccessPoint
nmcli con add type wifi ifname wlan0 mode ap con-name AccessPoint ssid 120308045 autoconnect false
nmcli con modify AccessPoint 802-11-wireless.band bg
nmcli con modify AccessPoint 802-11-wireless.channel 3
nmcli con modify AccessPoint ipv4.method shared ipv4.address 192.168.4.1/24
nmcli con modify AccessPoint ipv6.method disabled

sleep 1

sudo nmcli con up AccessPoint

sleep 1

/home/arducam/bin/webInterface.py &

sleep 1

/home/arducam/bin/dockerDUFS.sh

sleep 1

touch /home/arducam/wifiUP.txt

# nmcli con down AccessPoint
