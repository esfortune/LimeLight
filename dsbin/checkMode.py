#!/usr/bin/python
# Copyright Eric Fortune, CanopyLife, April 2025 
# Code written for MothPad device.

# This code polls the sole user switch on the MothPad device.
# 
# If up we are in "Full Services" mode (default), if down we are in
# "Power Saver" mode. This code is run when crontab calls stepOne
# routine. A better version would be more responsive.

from gpiozero import Button

### Custom configuration file (gives GPIO pin identify of switch)
import config as c

# Define button
button = Button(c.switch_gpio)

# Our routine
def is_button_pressed():
    return button.is_pressed

# Print the result
if __name__ == "__main__":
    if is_button_pressed():
        print(f'PowerSaver')
        exit(0)
    else:
        print(f'FullService')
        exit(1)
