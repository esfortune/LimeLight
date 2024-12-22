#!/usr/bin/python
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.

# This code polls the sole user switch on the Limelight device.
# If up we are in collection mode (default), if down we are in
# download mode. This runs only when crontab calls the data 
# collection routine. A better version would be more responsive.

from gpiozero import Button

### Custom
import config as c

# Define button

button = Button(c.switch_gpio)

def is_button_pressed():
    return button.is_pressed

# Print the result
if __name__ == "__main__":
    if is_button_pressed():
        print(f'Button is pressed: 0 Download')
        exit(0)
    else:
        print(f'Button is not pressed: 1 Collect')
        exit(1)
