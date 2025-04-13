#!/bin/bash
# Uses djpeg to reduce the size of images as a step before making timelapse videos.
# This relies on the "parallel" command, but the old one-at-a-time loop code is preserved.

# Create the output directory if it doesn't exist
mkdir -p smaller

## Parallel processing method (this uses 8 cores)
parallel -j 4 'djpeg -scale 1/8 {} > smaller/{/.}.pnm' ::: *.jpg

## Loop through all jpg images in the current directory, one process at a time
#for img in *.jpg; do
#    # Check if any jpg files exist to avoid errors
#    [ -e "$img" ] || continue
#    
#    # Get the base filename without extension
#    base="${img%.*}"
#    
#    # Scale the image to 1/8 its original size and save as .pnm
#    djpeg -scale 1/8 "$img" > "smaller/$base.pnm"
#done

echo "Scaling complete. Images saved in 'smaller' directory."

