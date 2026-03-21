#!/usr/bin/python3
# Copyright Eric Fortune, CanopyLife, March 2026
# Code written for MothPad device.
#
# Monitors the user switch (GPIO) and controls the WiFi AccessPoint.
# Switch open/high/up  (FullService)  -> AccessPoint UP
# Switch closed/low/down (PowerSaver) -> AccessPoint DOWN
#
# Install to /usr/local/bin/switchMonitor.py
# Enable with: sudo systemctl enable switchMonitor.service

import signal
import subprocess
import sys

sys.path.insert(0, '/home/canopylife/bin')
import config as c

from gpiozero import Button

button = Button(c.switch_gpio)


def ap_up():
    subprocess.run(['nmcli', 'connection', 'up', 'AccessPoint'])


def ap_down():
    subprocess.run(['nmcli', 'connection', 'down', 'AccessPoint'])


# Set state to match current switch position on startup
if button.is_pressed:
    ap_down()
else:
    ap_up()

# React to future switch changes
button.when_released = ap_up    # switch opens  (high/up)  -> AP on
button.when_pressed  = ap_down  # switch closes (low/down) -> AP off

signal.pause()
