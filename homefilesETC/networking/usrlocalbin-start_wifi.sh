#!/bin/bash

# Always start hotspot (AP)
nmcli con up AccessPoint

# Give NetworkManager time
sleep 5

# Try to connect to known Wi-Fi (will autoconnect if previously saved)
nmcli networking connectivity check

