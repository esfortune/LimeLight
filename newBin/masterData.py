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
# Our functions

### Check to see if the WiFi is up or down (cheesy)
def ISwifiUP():
    return os.path.exists(c.wifiPathName)


####################################################################
### Check to see which mode: FullService (1) or PowerSaver (0)
currentMode = subprocess.run([checkMode], capture_output=True, text=True)


####################################################################
# DATA COLLECTION MODE
# When the pin is pulled up (released), run the shell script(s)

if currentMode.returncode == 1:
    print(f"DATA COLLECTION MODE")

    # If the backup was just completed, refresh the eINK screen for good measure.
    if not checkAlreadyCopied():
        subprocess.run([eINKupdate], check=True)

    # If data download mode exits uncleanly and leaves the tracking file, which is a common outcome,
    # then we won't be able to backup. So the user just needs to put it into
    # collection mode and this routine will remove the tracking file that prevents double copying.
    if check_file_exists():
        print(f'{file2CheckPathName} exists, but we are in data collection mode. DELETE!')
        os.remove(file2CheckPathName)
        ledBlink = subprocess.Popen([statusLED, '5'])
        exit(0)

    ########## MANAGING THE WIFI IS LIKELY TO CHANGE
    ########## FEB 11, 2025: rc.local removes the wifiUP.txt file
    ########## Both collection and download modes check to start WiFi
    # If the WiFi is on, turn it off (saves power during data collection mode)
    #if ISwifiUP():
    #    subprocess.run([wifiDN])
    ##### WE USED TO DO THIS AUTOMATICALLY.  NOW WE WAIT FOR THE USER TO DO IT.
    # Turn on the WiFi if it isn't already up
    if not ISwifiUP():
        subprocess.run(["sudo", wifiUP])

       

########################################## 
# Collect the datums

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


####################################################################
# DATA DOWNLOAD MODE

if currentMode.returncode == 0:
    print(f"DATA DOWNLOAD MODE")

    # Update the text message for the WiFi users
    subprocess.run([c.msgGenerator], check=True) 

    # Turn on the WiFi if it isn't already up
    if not ISwifiUP():
        subprocess.run(["sudo", wifiUP])

    # This code is routinely called by crontab while another instance is running.
    # We don't want to run a second consecutive instance, so exit cleanly.
    # Also checks to see if we have already backed up - don't run again!
    if check_file_exists():
        print(f'Copying already in process.')
        ledBlink = subprocess.Popen([statusLED, '4'])
        exit(0)

    # If this file is missing, it means that we haven't had any new data 
    if not checkAlreadyCopied():
        print(f'Copying already completed.')
        exit(0)

