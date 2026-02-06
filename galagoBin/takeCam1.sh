#!/bin/sh
## On a 2 camera system RPi5 system, take a photo using camera 1
# Save the image with a timestamp and the name C0-
# We are currently rotating 90 degrees for use in image merging.
#
# These two scripts would be better merged into a single that accepts
# an argument as to which camera to use. *sigh*

rpicam-still --camera 1 -n -o /tmp/cam1.jpg

timestamp=$(date +"%Y%m%d%H%M")

if [ -f /tmp/cam1.jpg ]; then
    convert /tmp/cam1.jpg -rotate 90 C1-$timestamp.jpg
    exit 0
else
    echo "Error: Something is wrong with camera 1.\n"
    exit 1
fi
