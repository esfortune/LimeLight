#!/bin/bash
# This script renames the jpg files taken using the studio to have more identifiable
# information. Harold "demanded" this be done. And he was right.
# The original filename has the date and time (but not the year)

# We store the location in the first line of the /home/arducam/location.txt file.
# We have the tr command in case the user was an idiot (like me) and had spaces or other
# special characters in there.
location=$(head -1 /home/arducam/location.txt | tr -cd '[:alnum:]')

# Get the device serial number from /home/arducam/serialNumber.txt
serialNum=$(head -1 /home/arducam/serialNumber.txt | tr -cd '[:alnum:]')

# Get the current date in MM-DD-YYYY format
yearstr=$(date +"%Y")

# Loop through all jpg files in the current directory and change their names
for file in *.jpg; do
    # Ensure the file exists to prevent errors when no .jpg files are present
    [ -e "$file" ] || continue
    
    # Rename the file to location_serialnumber_year_originalfilename.jpg
    mv "$file" "${location}_${serialNum}_${yearstr}_${file}"
done
