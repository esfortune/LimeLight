# LimeLight
Limelight development, Updated 21-October-2024

This is code to run on an RPi•5 Limelight controller. 

This includes code for data aquisition and management.

Data currently include the Insect studio, MicroMoth USB Audio, and GPS.

Plan to add basic environmental data (temperature, humidity, etc.)


Uses a combination of Python and shell (/bin/sh) scripts controlled by crontab.

---

# Hardward details

Ultimate GPS Hat (Adafruit)

AudioMoth USB Microphone (384kHz sample rate)

Arducam Owlsight camera (64MP)

"Acquisition / Download" DPDT switch [GPIO]

Studio Illumination (latching relay) [GPIO]

Attractor Illumination (latching relay) [GPIO]

---

# Code details

Code in /home/arducam/bin

Data in /home/arducam/data

Backups in /home/arducam/data/backups

USB mount /mnt/usb (see fstab)

## List of files

• **config.py**		Paths, defaults, and locations of helper code.

• **crontab.txt**		A sample contrab with logging.

• **checkMode.py**		This reports the status of the user switch.

• **checkUSBcopySpace.py**	Compares data directory to USB space prior to copy.

• **dataCollection.py**	The main script called by crontab.

• **takeAudioSample.sh**	Takes an Audio sample via USB microphone.

• **takeGPS.sh**		Reads the GPS Hat and logs the data.

• **takeStudioPhoto.sh**	Takes a photo using libcamera-still.

• **mountUSB.sh**		Mounts the USB drive for backups.

• **umountUSB.sh**		Unmounts the USB drive.

• **usbFileManagement.py**	Manages data handling for backups to USB drives.

• **statusBlinker.py**	Drives the LED status signals.

• **dockerDUFS.sh**		The web interface (port 5000) available on wlan0 and eth0.

---

# USAGE

Indicator LEDs (Power, Switch, Status via NEOPIXEL)

