#!/bin/bash

# Enable dual-mode hotspot and attempt connection to known Wi-Fi
set -e

logger "[wifi_dual_mode] Starting dual-mode setup..."

# Ensure the hotspot exists and is configured
if nmcli con show AccessPoint &>/dev/null; then
  nmcli con delete AccessPoint
fi

nmcli connection add type wifi ifname wlan0 con-name AccessPoint ssid AccessPoint \
    mode ap ipv4.method manual ipv4.addresses 192.168.4.1/24 802-11-wireless.band bg

nmcli connection modify AccessPoint connection.autoconnect yes

# Bring up hotspot
nmcli connection up AccessPoint

# Let NetworkManager try autoconnecting to known networks
sleep 5

# Check if a Wi-Fi (STA mode) connection is also active
wifi_sta=$(nmcli -t -f NAME,DEVICE,TYPE connection show --active | grep ':wlan0:wifi' | grep -v AccessPoint | cut -d: -f1)

if [ -n "$wifi_sta" ]; then
  logger "[wifi_dual_mode] Connected to Wi-Fi network: $wifi_sta"
else
  logger "[wifi_dual_mode] No known Wi-Fi connected; remaining in AP mode only"
fi

