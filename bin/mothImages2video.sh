#!/bin/bash

# Create the output directory if it doesn't exist
echo "Making directory: smaller4video."

mkdir -p smaller4video
sleep 1

# Loop through all of the images, using djpeg for 1/8th scaling
echo "Looping through original images."

# Function to process a single image
process_image() {
    img="$1"
    base="${img%.*}"
    djpeg -scale 1/8 "$img" > "smaller4video/$base.pnm"
}

# Export function so it can be used by parallel
export -f process_image

# Find all jpg files and process them using up to 8 parallel jobs
find . -maxdepth 1 -type f -name "*.jpg" | xargs -P 8 -I {} bash -c 'process_image "$1"' _ {}

# find . -maxdepth 1 -type f -name "*.jpg" | parallel -j8 process_image

echo "Scaling complete. Images saved in 'smaller4video' directory."


# Loop through all of the images, using djpeg for 1/8th scaling
##echo "Looping through original images."

# Loop through all jpg images in the current directory
## for img in *.jpg; do
    ## # Check if any jpg files exist to avoid errors
    ## [ -e "$img" ] || continue
    ## 
    ## # Get the base filename without extension
    ## base="${img%.*}"
    ## 
    ## # Scale the image to 1/8 its original size and save as .pnm
    ## djpeg -scale 1/8 "$img" > "smaller4video/$base.pnm"
## done
## 
## echo "Scaling complete. Images saved in 'smaller4video' directory."
## sleep 1

# We use ffmpeg to make the video from the image sequence.

echo "Making video using ffmpeg."
cd smaller4video

ffmpeg -framerate 30 -pattern_type glob -i '*.pnm' -c:v libx264 -pix_fmt yuv420p mothvideo.mp4

echo "Processing complete. Enjoy the video!!!"
cd ..

exit 0
