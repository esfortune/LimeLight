#!/bin/sh
#
# This is the central function of the Galago (Bush Baby) version of the
# CanopyLife device -- to take two photos of the Moth area and merge
# them. This is the worst programming -- I am deeply embaarassed by
# what follows.

# We want to take two simultaneous images. What I've done is an abomonation.
# The first image is taken with camera 0 and spawned so that the script 
# rapidly gets to the second camera.
rpicam-still --camera 0 -n -o /tmp/cam0.jpg &
rpicam-still --camera 1 -n -o /tmp/cam1.jpg 

# But I don't spawn the second camera so that it forces the rest of the script
# to wait until it is done. BUT... sometimes the first process takes longer
# to complete than the second, so instead of solving the issues I do this
# stoopid step... sleep for a few seconds.  How dumb is that?

sleep 5 

# We want to save the original and merged images with a time stamp...
timestamp=$(date +"%Y%m%d%H%M")

# Before proceeding, we make sure that the images were taken. Cameras are a common
# point of failure.
if [ -f /tmp/cam0.jpg ]; then
    convert /tmp/cam0.jpg -rotate 90 /tmp/C0-$timestamp.jpg
    rm /tmp/cam0.jpg
else
    echo "Error: Something is wrong with camera 0.\n"
fi

if [ -f /tmp/cam1.jpg ]; then
    convert /tmp/cam1.jpg -rotate 90 /tmp/C1-$timestamp.jpg
    rm /tmp/cam1.jpg
else
    echo "Error: Something is wrong with camera 1.\n"
fi

# If both images are available, make the merged image
if [ -f /tmp/C0-$timestamp.jpg ]; then
    if [ -f /tmp/C1-$timestamp.jpg ]; then
        /home/canopylife/bin/automerger.py /tmp/C0-$timestamp.jpg /tmp/C1-$timestamp.jpg
        mv /tmp/merged_result.jpg merged-$timestamp.jpg
        mv /tmp/C0-$timestamp.jpg .
        mv /tmp/C1-$timestamp.jpg .
    fi
fi


# A major problem with this script is that it saves the data into the
# $pwd. It should accept an argument for where to put the final images.
# Another point of failure is when the automerger.py script doesn't work.
# Need to add error catching there and frankly, replace the Python
# script for merging with something better.

