#!/bin/bash
# Version 1 from https://forums.raspberrypi.com/viewtopic.php?t=357998

nmcli con delete AccessPoint
nmcli con add type wifi ifname wlan0 mode ap con-name AccessPoint ssid 117722760 autoconnect false
nmcli con modify AccessPoint 802-11-wireless.band bg
nmcli con modify AccessPoint 802-11-wireless.channel 3
nmcli con modify AccessPoint 802-11-wireless.cloned-mac-address 00:12:34:56:78:9a
nmcli con modify AccessPoint ipv4.method shared ipv4.address 192.168.4.1/24
nmcli con modify AccessPoint ipv6.method disabled
nmcli con modify AccessPoint wifi-sec.key-mgmt wpa-psk
nmcli con modify AccessPoint wifi-sec.psk "117722760"
nmcli con up AccessPoint

touch /home/arducam/wifiUP.txt

sleep 1

/home/arducam/bin/dockerDUFS.sh

# nmcli con down AccessPoint
