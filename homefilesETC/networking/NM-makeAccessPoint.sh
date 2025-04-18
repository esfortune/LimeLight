#!/bin/bash

nmcli connection add type wifi ifname wlan0 con-name AccessPoint autoconnect yes ssid 123456789 wifi.mode ap ipv4.method shared ipv4.addresses 192.168.4.1/24 802-11-wireless.band bg

nmcli connection modify AccessPoint connection.autoconnect yes

