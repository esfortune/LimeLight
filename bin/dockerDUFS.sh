#!/bin/sh
# Eric Fortune, Canopy Life, December 2024 
# Code written for Limelight Rainforest test device.
# This is a simple script to run DUFS via docker. This allows web access to our data directory
# via port 5000. I'm not sure that this is the way to handle this process, as I want it
# to come up and down. Currenlyt I can't get it to go away.  And I am struggling with the
# access point feature.

# -d runs in detached mode

docker run -d -v /home/arducam/data:/data -p 5000:5000 --rm sigoden/dufs /data -A


# docker run -v `pwd`:/data -p 5000:5000 --rm sigoden/dufs /data -A
