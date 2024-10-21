# LimeLight
Limelight development, Updated 7-October-2024

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

"Acquisition / Download" DPDT switch @ GPIO23

Studio Illumination GPIO12 (latching relay)

Attractor Illumination GPIO16 (latching relay)

---

# Code details

Code in /home/arducam/bin

Data in /home/arducam/data

Backups in /home/arducam/backup

USB mount /mnt/usb (see fstab)

## List of files

• **AudioRecording.sh**	Collects USB Audio data (30 seconds).

• **checkMode.py**		This reports the status of the user switch.

• **checkUSBcopySpace.py**	Compares data directory to USB space prior to copy.

• **config.py**		Paths, defaults, and helper code.

• **crontab.txt**		A sample contrab.

• **dataCollection.py**	The main script called by crontab.

• **dockerDUFS.sh**		The web interface (port 5000).

• **mountUSB.sh**		Mounts the USB drive for backups.

• **statusBlinker.py**	Drives the LED status signals.

• **takeAudioSample.sh**	Takes an Audio sample via USB microphone.

• **takeGPS.sh**		Reads the GPS Hat and logs the data.

• **takeStudioPhoto.sh**	Takes a photo using libcamera-still.

• **umountUSB.sh**		Unmounts the USB drive.

• **usbFileManagement.py**	Manages data handling for backups to USB drives.

---

# USAGE

Indicator LEDs (Power, Switch, Status via NEOPIXEL)

