#!/bin/bash
# Version 2 from https://forums.raspberrypi.com/viewtopic.php?t=357998

nmcli con delete AccessPoint
nmcli con add type wifi ifname wlan0 mode ap con-name AccessPoint ssid 117722760 autoconnect false
nmcli con modify AccessPoint wifi.band bg
nmcli con modify AccessPoint wifi.channel 3
nmcli con modify AccessPoint wifi.cloned-mac-address 00:12:34:56:78:9a
nmcli con modify AccessPoint wifi-sec.key-mgmt wpa-psk
nmcli con modify AccessPoint wifi-sec.proto rsn
nmcli con modify AccessPoint wifi-sec.group ccmp
nmcli con modify AccessPoint wifi-sec.pairwise ccmp
nmcli con modify AccessPoint wifi-sec.psk "117722760"
nmcli con modify AccessPoint ipv4.method shared ipv4.address 192.168.4.1/24
nmcli con modify AccessPoint ipv6.method disabled
nmcli con up AccessPoint
