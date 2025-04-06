#!/usr/bin/python
# Copyright Eric Fortune, CanopyLife, April 2025 
# Code written for MothPad device.
#
# This script checks the hardware switch: 1-FullService or 0-PowerSaver.
# FullService has web services, WiFi. PowerSaver only collects data.
# 
# User can temporarily turn off data collection via web services.
# We use config.py to guide to the right scripts to collect the appropriate data. 
# 
# We check to see if the drive is full before collecting more data. If full, turn
# on indicator LED warning and prevent further attempts at collection.
#
# This script accepts command line arguments to overide data collection defaults.
#
# Relies on config.py, which has list of dependent code and paths

import time
import subprocess
import shutil
import os
import sys


####################################################################
# Definitions from config.py

# Our configuration file
import config as c

# Define paths 

datadir = c.data_path                           # Where our data live
file2CheckPathName = c.file2CheckPathName       # We use this file to prevent double backup processes

# Define scripts

getStudioPhoto = c.samplePhoto                  # Path to photo script
getAudioSample = c.sampleAudio                  # Path to audio script
getGPS = c.sampleGPS                            # Path to GPS logger
getEnvironment = c.sampleEnvironment            # Path to env logger

checkMode = c.checkMode
statusLED = c.statusLED

# Set defaults for what data to collect (user can override below)
takeAudio = c.data_audio
takeEnvironment = c.data_environmental
takeGPS = c.data_gps
takeStudio = c.data_studio

# WiFi business   ####### THIS MAY BE SUBJECT TO CHANGE
wifiUP = c.wifiUPPER
wifiDN = c.wifiDOWNER
# we also use c.wifiPathName

####################################################################
### Check to see which mode: FullService (1) or PowerSaver (0)

currentMode = subprocess.run([checkMode], capture_output=True, text=True)

if currentMode == 1:           # Full services requested
    systemServices up

if currentMode == 0: .         # Power Saver Mode
    systemServices Down

    if not ISwifiUP():
        subprocess.run(["sudo", wifiUP])


####################################################################
# The user can override data defaults via command-line arguments.
# As of April 2025 we default to NO DATA streams in config.py.
# FUTURE: add error checking for the command line arguments.

if len(sys.argv) > 1:
    if "Audio" in sys.argv:
        takeAudio = 1
    if "NoAudio" in sys.argv:
        takeAudio = 0
    if "Studio" in sys.argv:
        takeStudio = 1
    if "NoStudio" in sys.argv:
        takeStudio = 0
    if "GPS" in sys.argv:
        takeGPS = 1
    if "NoGPS" in sys.argv:
        takeGPS = 0
    if "Env" in sys.argv:
        takeEnvironment = 1
    if "NoEnv" in sys.argv: 
        takeEnvironment = 0


####################################################################
# Finally, DATA COLLECTION 


if check_file_exists():

    if takeGPS == 1:
        try:
            subprocess.run([getGPS], check=True)
            print(f"Script {getGPS} executed successfully.")
        except subprocess.CalledProcessError as eg:
            print(f"Error running script: {eg}")

    if takeEnvironment == 1:
        try:
            subprocess.run([getEnvironment], check=True)
            print(f"Script {getEnvironment} executed successfully.")
        except subprocess.CalledProcessError as ea:
            print(f"Error running script: {ea}")
           
    if takeStudio == 1:
        try:
            subprocess.run([getStudioPhoto], check=True)
            print(f"Script {getStudioPhoto} executed successfully.")
        except subprocess.CalledProcessError as es:
            print(f"Error running script: {es}")

    if takeAudio == 1:
        try:
            subprocess.run([getAudioSample], check=True)
            print(f"Script {getAudioSample} executed successfully.")
        except subprocess.CalledProcessError as ea:
            print(f"Error running script: {ea}")


        ledBlink = subprocess.Popen([statusLED, '4'])
        exit(0)

