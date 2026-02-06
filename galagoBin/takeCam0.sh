#!/bin/sh
## On a 2 camera system RPi5 system, take a photo using camera 0
# Save the image with a timestamp and the name C0-
# We are currently rotating 90 degrees for use in image merging.

rpicam-still --camera 0 -n -o /tmp/cam0.jpg

timestamp=$(date +"%Y%m%d%H%M")

if [ -f /tmp/cam0.jpg ]; then
    convert /tmp/cam0.jpg -rotate 90 C0-$timestamp.jpg
    exit 0
else
    echo "Error: Something is wrong with camera 0.\n"
    exit 1
fi
