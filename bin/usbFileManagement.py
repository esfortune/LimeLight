#!/usr/bin/python
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test devices.
#
# This code detects the presence of a USB. If not, use LED to prompt
# the user to insert one. Mount the USB and then check to see if there
# is sufficient space. Copy the data from curdat to the USB, and then
# move curdat to another directory for safe keeping.

import shutil
import time
import os
import subprocess

### Our configuration

import config as c

# Define source and destination paths
usb_device = c.usb_dev
datadir = c.data_path  # Modify this if your directory is different
usbdrive = c.usb_path  # Update this to match your USB mount point
backupPath = c.backup_path

timestamp = time.strftime("%Y%b%d-%H%M%S")
backupDirectory = os.path.join(backupPath, timestamp)
usbDirectory = os.path.join(usbdrive, timestamp)

# Helper programs
sudoMount = c.mountusb
sudoUmount = c.umountusb
statusLED = c.statusLED
checkUSBcopy = c.checkUSBcopy

file2CheckPathName = c.file2CheckPathName

####################################################
# The copy process can be quite long, and so crontab
# might intiate another copy before the initial copy
# is complete. By touching this file, we prevent
# double copying.

print(f"Touching control file.")
f = open(file2CheckPathName, 'w')
f.write('File copy process initiated. \n')
f.close()

################### Check if USB is mounted
def is_drive_mounted(device):
    """Check if the specified device is mounted."""
    with open('/proc/mounts', 'r') as mounts:
        for line in mounts:
            if device in line:
                return True
    return False

################### Check if USB has sufficient space
def is_enough_space():
    """Check if USB has sufficient space."""
    enoughSpace = subprocess.run([checkUSBcopy])
    if enoughSpace.returncode == 0:
        return True
    if enoughSpace.returncode == 1:
        return False

#################### Mount USB device routine
def sudo_mount():

    try:
        # Run the shell script with sudo
        result = subprocess.run(['sudo', sudoMount], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running the script as sudo: {e}")
        print(f"Script error output: {e.stderr}")

#################### unMount USB device routine
def sudo_umount():

    try:
        # Run the shell script with sudo
        result = subprocess.run(['sudo', sudoUmount], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    except subprocess.CalledProcessError as e:
        print(f"Error running the script as sudo: {e}")
        print(f"Script error output: {e.stderr}")

#################### Copy files to USB routine
def copy_files_to_usb():
    """Copy files from the curdat directory to the USB drive."""

    ### Make sure that the USB drive is mounted (check and if not, prompt user)
    testit = 0
    while not is_drive_mounted(usb_device):
        testit += 1
        print(f"Waiting for {usb_device} to be mounted...")
        ledBlink = subprocess.Popen([statusLED, '2'])
        sudo_mount()
        time.sleep(10)  # Wait 10 seconds before checking again
        ledBlink.kill()
        if testit > 3: # Give up after 40 seconds
            exit(1)

    ### Make sure that there is enough space on USB (check and if not, prompt user to replace)
    if not is_enough_space():
        print(f"Oops - {usb_device} is too full... please replace")
        sudo_umount()
        ledBlink = subprocess.Popen([statusLED, '3'])
        time.sleep(10)
        print(f"Removing tracking file because there was insufficient space.")
        os.remove(file2CheckPathName)
        ledBlink.kill()
        time.sleep(1)
        ledBlink = subprocess.Popen([statusLED, '6'])
        exit(1)

    ####################################################
    ### Loop through files in the source data directory and copy to USB
    ### No longer a loop.  Need to have some error catcing step here.

    print(f"Device {usb_device} is mounted, copying files")
    ledBlink = subprocess.Popen([statusLED, '1'])

    ### FUCK ALL IF the gpio pipe doesn't fuck things up.  Remove the file if it appears.
    file_LGpath1 = '/home/arducam/data/curdat/.lgd-nfy0'
    file_LGpath2 = '/home/arducam/data/curdat/Studio/.lgd-nfy0'

    if os.path.exists(file_LGpath1):
        os.remove(file_LGpath1)
        print(f"File '{file_LGpath1}' deleted successfully.")
    else:
        print(f"File '{file_LGpath1}' not found.")

    if os.path.exists(file_LGpath2):
        os.remove(file_LGpath2)
        print(f"File '{file_LGpath2}' deleted successfully.")
    else:
        print(f"File '{file_LGpath2}' not found.")
    ### FUCK ALL IF the gpio pipe doesn't fuck things up.  Remove the file if it appears. LGDeleter.py


    shutil.copytree(datadir, usbDirectory, dirs_exist_ok=True)

    print(f"Copying to USB.")

    print(f"Syncing data to USB.")
    os.sync()
    time.sleep(1)

    ####################################################
    ### Move data to backup directory

    print(f"Moving the data to the Backup directory")
    os.makedirs(backupDirectory, exist_ok=True)
    shutil.move(datadir, backupDirectory)
    time.sleep(5)
    os.makedirs(datadir, exist_ok=True)

    print(f"Copy complete, waiting 5 seconds and unmounting USB drive.")
    time.sleep(5)
    ledBlink.kill()
    sudo_umount()
    time.sleep(1)
    ledBlink = subprocess.Popen([statusLED, '6'])

    print(f"Removing tracking file.")
    os.remove(file2CheckPathName)
    print(f"Done.")

####################################################
############ Run the script (This is ass backwards, need to fix)

print(f"Initiating file copy routine.")
copy_files_to_usb()

