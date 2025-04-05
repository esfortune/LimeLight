#!/usr/bin/python
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.


# Setting the serial number as the RustDesk identity
# /home/arducam/serialNumber.txt only has 9 digit RustDesk number
try:
    with open("/home/arducam/serialNumber.txt", "r") as file:
        deviceSerial = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default serial number
    deviceSerial = "D27_Serial"

### Paths

backup_path = '/home/arducam/data/backups'
base_path = '/home/arducam'
bin_path = '/home/arducam/bin'
data_path = '/home/arducam/data/curdat'
usb_dev = '/dev/sda1'
usb_path = '/mnt/usb'
file2CheckPathName = '/home/arducam/FileCopyInitiated.txt'
wifiPathName = '/home/arducam/wifiUP.txt'
stemma_csvfile = '/home/arducam/data/curdat/stemmadat.csv'
datalogfile = '/home/arducam/data/curdat/dataLog.csv'

### Helper programs

samplePhoto = '/home/arducam/bin/takeStudioPhoto.sh' # Photograph (also controls LEDs)
sampleAudio = '/home/arducam/bin/takeAudioSample.sh' # Audio Sample (ultrasonic microphone)
sampleGPS = '/home/arducam/bin/takeGPS.sh' # Get data from GPS device
sampleEnvironment = '/home/arducam/bin/stemmaData.py' # Get data from environmental sensor package
wifiUPPER = '/home/arducam/bin/wifiV1.sh'
wifiDOWNER = '/home/arducam/bin/wifiV1down.sh'
msgGenerator = '/home/arducam/bin/msgGenerator.sh'

checkMode = '/home/arducam/bin/checkMode.py' # Decides whether we are in COLLECT (1) or DOWNLOAD (0) mode
checkUSBcopy = '/home/arducam/bin/checkUSBcopySpace.py' # Checks to see if sufficient space to copy to USB
fileBackup = '/home/arducam/bin/usbFileManagement.py' # Copies files to USB and manages internal data

mountusb = '/home/arducam/bin/mountUSB.sh'
umountusb = '/home/arducam/bin/umountUSB.sh'

statusLED = '/home/arducam/bin/statusBlinker.py'
eINKupdate = '/home/arducam/bin/eINKstatus.py'

### Which GPIO pins will we use?

attractorON_gpio = 16 # LEDs to attract moths
attractorOFF_gpio = 13 # LEDs to attract moths
studioON_gpio = 12 # LEDs for photographs
studioOFF_gpio = 6 # LEDs for photographs
switch_gpio = 23 # User switch for COLLECT or DOWNLOAD modes

### Which data do we want to collect for default? (1 for yes, 0 for no)

data_audio = 0
data_environmental = 0
data_gps = 0
data_studio = 0

# Interval to collect data (in seconds)?
crontab_interval = 30

