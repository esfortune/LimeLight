#!/bin/bash

# Create the output directory if it doesn't exist
mkdir -p smaller

# Loop through all jpg images in the current directory
for img in *.jpg; do
    # Check if any jpg files exist to avoid errors
    [ -e "$img" ] || continue
    
    # Get the base filename without extension
    base="${img%.*}"
    
    # Scale the image to 1/8 its original size and save as .pnm
    djpeg -scale 1/8 "$img" > "smaller/$base.pnm"
done

echo "Scaling complete. Images saved in 'smaller' directory."
