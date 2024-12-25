#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
# This is code for recording from the current microphone, which is
# an Audiomoth flashed as a microphone, on a Raspberry Pi 5. 
# 384000 Hz sample rate, 60 sec duration.

arecord -D hw:CARD=Microphone,DEV=0 -f S16_LE -r 384000 -d 60 /home/arducam/foobar.wav
