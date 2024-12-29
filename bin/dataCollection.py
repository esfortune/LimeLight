#!/usr/bin/python
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
#
# This script checks the Mode: 1-collection or 0-download
# If collection, use config.py to guide to the right scripts to
# collect the appropriate data. Check to see if the drive is full.
# The code can also accept command line arguments to turn off data collection
# If download, it runs usbFileManagement.py to download.
#
# Code relies on config.py, which has list of dependent code and paths

import time
import subprocess
import shutil
import os
import sys

### Our configuration file

import config as c

#### Definitions

# Define paths and scripts
datadir = c.data_path # Where our data live
studioPhoto = c.samplePhoto # Path to photo script
audioSample = c.sampleAudio # Path to audio script
getGPS = c.sampleGPS # Path to GPS logger
getEnvironment = c.sampleEnvironment # Path to env logger
file2CheckPathName = c.file2CheckPathName # We use this file to prevent double backup processes

checkMode = c.checkMode
backupProcess = c.fileBackup  

statusLED = c.statusLED
eINKupdate = c.eINKupdate

# What data to collect (user can reject data streams)
takeAudio = c.data_audio
takeEnvironment = c.data_environmental
takeGPS = c.data_gps
takeStudio = c.data_studio

# WiFi business
wifiUP = c.wifiUPPER
wifiDN = c.wifiDOWNER
# we also use c.wifiPathName

####################################################################
# The user can eliminate one of the data streams - for now this will 
# is limited to just ONE function - just turning off Audio or Studio usually.
# In the future, the user can over-ride more than one default found in config.py

if len(sys.argv) > 1:
    if "NoAudio" in sys.argv:
        takeAudio = 0
    if "NoStudio" in sys.argv:
        takeStudio = 0
    if "NoGPS" in sys.argv:
        takeGPS = 0
    if "NoEnv" in sys.argv:
        takeEnvironment = 0

########################################## 
# Our functions

### Check to see the status of the copy-to-usb process
# to prevent duplicate simultaneous copying
def check_file_exists():
    return os.path.exists(file2CheckPathName)

### Check if we just completed the copy process
# To tell data collection mode to do an update etc
def checkAlreadyCopied():
    return os.path.exists(c.datalogfile)

### Check to see if the WiFi is up or down (cheesy)
def ISwifiUP():
    return os.path.exists(c.wifiPathName)


####################################################################
### Check to see which mode: data collection (1) or data download (0)
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

    # If the WiFi is on, turn it off (saves power during data collection mode)
    if ISwifiUP():
        subprocess.run([wifiDN])
       

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
            subprocess.run([studioPhoto], check=True)
            print(f"Script {studioPhoto} executed successfully.")
        except subprocess.CalledProcessError as es:
            print(f"Error running script: {es}")

    if takeAudio == 1:
        try:
            subprocess.run([audioSample], check=True)
            print(f"Script {audioSample} executed successfully.")
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
        subprocess.run([wifiUP])

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

########################################## 
# FINALLY - initiate the backup.

    print(f'Start copying process.')
    subprocess.run([eINKupdate], check=True)
    try:
        subprocess.run([backupProcess], check=True)
        print(f"Script {backupProcess} executed successfully.")
    except subprocess.CalledProcessError as es:
        print(f"Error running script: {es}")
