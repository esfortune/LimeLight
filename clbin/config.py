#!/usr/bin/python
# Copyright Eric Fortune, CanopyLife, April 2025
# Code written for MothPad device.


# Setting the serial number as the RustDesk identity
# /home/canopylife/serialNumber.txt only has 9 digit RustDesk number

try:
    with open("/home/canopylife/serialNumber.txt", "r") as file:
        deviceSerial = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default serial number
    deviceSerial = "001100110"

try:
    with open("/home/canopylife/location.txt", "r") as file:
        deviceLocation = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default location
    deviceLocation = "LocationIsNotSet"

try:
    with open("/home/canopylife/gps.txt", "r") as file:
        deviceGPS = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default location
    deviceGPS = "00d 00m S 00d 00m W"


### Paths

base_path = '/home/canopylife'
bin_path = '/home/canopylife/bin'
data_path = '/home/canopylife/data/curdat'
backup_path = '/home/canopylife/data/backups'

pause_data_collection = '/home/canopylife/tokens/dataPause.txt'
wifiPathName = '/home/canopylife/tokens/wifiStatus.txt'
env_csvfile = '/home/canopylife/data/curdat/ENVdata.csv'
datalogfile = '/home/canopylife/data/curdat/dataLog.csv'

### Helper programs

samplePhoto = '/home/canopylife/bin/takeStudioPhoto.sh' # Photograph (also controls LEDs)
sampleAudio = '/home/canopylife/bin/takeAudioSample.sh' # Audio Sample (ultrasonic microphone)
sampleGPS = '/home/canopylife/bin/takeGPS.sh' # Get data from GPS device
sampleEnvironment = '/home/canopylife/bin/takeENV.py' # Get data from environmental sensor package

wifiUPPER = '/home/canopylife/bin/wifiV1.sh'
wifiDOWNER = '/home/canopylife/bin/wifiV1down.sh'
msgGenerator = '/home/canopylife/bin/msgGenerator.sh'

checkMode = '/home/canopylife/bin/checkMode.py' # Decides whether we are in COLLECT (1) or DOWNLOAD (0) mode

statusLED = '/home/canopylife/bin/statusBlinker.py'
eINKupdate = '/home/canopylife/bin/eINKstatus.py'

### Which GPIO pins will we use?

attractorON_gpio = 16                                 # LEDs to attract moths ON
attractorOFF_gpio = 13                                # LEDs to attract moths OFF
studioON_gpio = 12                                    # LEDs for photographs ON
studioOFF_gpio = 6                                    # LEDs for photographs OFF

switch_gpio = 23                                      # User switch for COLLECT or DOWNLOAD modes

### Which data do we want to collect for default? (1 for yes, 0 for no)

data_audio = 0
data_environmental = 0
data_gps = 0
data_studio = 0

