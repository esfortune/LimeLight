#!/usr/bin/python
# Copyright Eric Fortune, CanopyLife, June 2025
# Code written for MothPad device.


#######################################
# Set the serial number 

try:
    with open("/home/canopylife/serialNumber.txt", "r") as file:
        deviceSerial = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default serial number
    deviceSerial = "001100110"

#######################################
# Set the location 

try:
    with open("/home/canopylife/location.txt", "r") as file:
        deviceLocation = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default location
    deviceLocation = "LocationIsNotSet"

#######################################
# Set the Lat/Long (gps)

try:
    with open("/home/canopylife/gps.txt", "r") as file:
        deviceGPS = file.readline().strip()
except FileNotFoundError:
    # If the file does not exist, use a default location
    deviceGPS = "Location not set"

#######################################
# Set the paths on the MothPad device

### Paths

base_path = '/home/canopylife'
bin_path = '/home/canopylife/bin'
data_path = '/home/canopylife/data/curdat'
backup_path = '/home/canopylife/data/Jotta'

pause_data_collection = '/home/canopylife/tokens/dataPause.txt'
wifiPathName = '/home/canopylife/tokens/wifiStatus.txt'
env_csvfile = '/home/canopylife/data/curdat/ENVdata.csv'
datalogfile = '/home/canopylife/data/curdat/dataLog.csv'

#######################################
# Helper programs

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

#######################################
# Which GPIO pins will we use?

attractorON_gpio = 16                                 # LEDs to attract moths ON
attractorOFF_gpio = 13                                # LEDs to attract moths OFF
studioON_gpio = 12                                    # LEDs for photographs ON
studioOFF_gpio = 6                                    # LEDs for photographs OFF

switch_gpio = 23                                      # User switch for COLLECT or DOWNLOAD modes

# Status LED (statusBlinkerNP.py / statusBlinkerDS.py).  These do NOT use SPI,
# so the SPI0 bus (GPIO 8-11) is left entirely to the AD HAT.
# NeoPixel and DotStar devices are never fitted together, so they share GPIO 26.
statusNeoPixel_gpio = 26                              # NeoPixel data in (DIN), physical pin 37 (Pi 5 PIO)
statusDotStarData_gpio = 26                           # DotStar data in (DI), physical pin 37
statusDotStarClock_gpio = 5                           # DotStar clock in (CI), physical pin 29

# Pins already taken by other hardware - do not reuse:
#   GPIO 0, 1    HAT ID EEPROM (ID_SD / ID_SC)
#   GPIO 2, 3    I2C (Witty Pi 5 HAT+, sensors)
#   GPIO 7-11    SPI0 (Waveshare High-Precision AD HAT; CE1 on GPIO 7 is claimed by the SPI driver)
#   GPIO 14, 15  UART0 (dtparam=uart0=on)
#   GPIO 17, 18, 22  AD HAT DRDY, RESET, CS
#   GPIO 6, 12, 13, 16, 23  see above
#   GPIO 24, 25  avoided: used by Waveshare e-Paper HATs (BUSY, DC)
#   GPIO 19-21   avoided: I2S audio / SPI1
# Still free: GPIO 4, 27

#######################################
### Which data do we want to collect for default? (1 for yes, 0 for no)

data_audio = 0
data_environmental = 0
data_gps = 0
data_studio = 0

