#!/bin/bash
# Uses djpeg to reduce the size of images as a step before making timelapse videos.
# This relies on the "parallel" command.

workingDIR=$1
datestamp=$2
location=$(head -1 /home/canopylife/location.txt | tr -cd '[:alnum:]')
serial=$(head -1 /home/canopylife/serialNumber.txt | tr -cd '[:alnum:]')

# datestamp=$(date +"%Y%b%d")

if [ -d "$workingDIR" ]; then

   cd $workingDIR/Studio

   # Create the temporary output directory if it doesn't exist
   mkdir -p smaller

   ## Parallel processing method (this uses 4 cores)
   parallel -j 4 'djpeg -scale 1/8 {} > smaller/{/.}.pnm' ::: *.jpg

   echo "Scaling complete. Images saved in 'smaller' directory."

   cd smaller

   # Generate SRT subtitle file mapping each frame to its original .jpg filename
   ls -1 *.pnm | sort | awk '{
       label = substr($0, 1, length($0)-4) ".jpg"
       n = NR - 1
       s = int(n * 1000 / 30)
       e = int((n + 1) * 1000 / 30)
       printf "%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n%s\n\n",
           NR,
           int(s/3600000), int((s%3600000)/60000), int((s%60000)/1000), s%1000,
           int(e/3600000), int((e%3600000)/60000), int((e%60000)/1000), e%1000,
           label
   }' > subtitles.srt

   ffmpeg -framerate 30 -pattern_type glob -i '*.pnm' \
       -vf "subtitles=subtitles.srt:force_style='FontSize=10,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1,Shadow=0,Alignment=1,MarginL=10,MarginV=10'" \
       -c:v libx264 -pix_fmt yuv420p output.mp4

   rm subtitles.srt

#   mv output.mp4 "../${serial}_${location}_${datestamp}.mp4"  ### Old MOVER

    dest_base="../${serial}_${location}_${datestamp}"
    dest_file="${dest_base}.mp4"

    # Check if the file already exists, and if so, keep going until we have a new unique name
    suffix=a
    while [ -e "$dest_file" ]; do
        dest_file="${dest_base}-${suffix}.mp4"
        suffix=$(echo "$suffix" | tr "0-9a-y" "1-9a-z")
    done

    # Move with final unique name
    mv output.mp4 "$dest_file"

   cd ..
   rm -rf smaller

else
   echo "Directory not found"
fi
