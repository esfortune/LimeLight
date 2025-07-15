#!/bin/bash
# Reads the GPS data from the Goouuu Tech GT-07 device (U-Blox AG [u-blox 7])
# and puts it into human-readable format

DEVICE="/dev/ttyACM0"
OUTPUT="$HOME/data/curdat/gps_log.csv"

# Add CSV header if file doesn't exist
if [ ! -f "$OUTPUT" ]; then
    echo "timestamp,latitude,longitude,altitude_meters" >> "$OUTPUT"
fi

timeout 10 cat $DEVICE > /tmp/gpsdata.txt
# Read one GPRMC sentence from the device
GPRMC_LINE=$(grep "\$GPRMC" /tmp/gpsdata.txt | tail -n 1)
GPGGA=$(grep "\$GPGGA" /tmp/gpsdata.txt | tail -n 1)

if [ -z "$GPRMC_LINE" ]; then
    echo "No GPRMC data received."
    exit 1
fi

IFS=',' read -r _ time_str status lat lat_dir lon lon_dir _ _ date_str _ <<< "$GPRMC_LINE"

# Only use valid fix
if [ "$status" != "A" ]; then
    echo "Invalid GPS fix."
    exit 1
fi

# Convert time: HHMMSS.SS and DDMMYY to YYYY-MM-DD HH:MM:SS
hh=${time_str:0:2}
mm=${time_str:2:2}
ss=${time_str:4:2}
dd=${date_str:0:2}
mo=${date_str:2:2}
yy=${date_str:4:2}
yyyy=$((2000 + 10#$yy))
timestamp="$yyyy-$mo-$dd $hh:$mm:$ss"

# Function to convert lat/lon to decimal
convert_coord() {
    val="$1"
    dir="$2"
    deg=${val%.*}
    min=${val#${deg}}
    deg_len=$(( ${#deg} - 2 ))
    d=${deg:0:$deg_len}
    m=${deg:$deg_len}${min}
    dec=$(echo "scale=6; $d + ($m / 60)" | bc -l)
    if [[ "$dir" == "S" || "$dir" == "W" ]]; then
        dec=$(echo "-1 * $dec" | bc -l)
    fi
    printf "%.6f" "$dec"
}

latitude=$(convert_coord "$lat" "$lat_dir")
longitude=$(convert_coord "$lon" "$lon_dir")

# Parse GPGGA for altitude
if [[ $GPGGA =~ \$GPGGA,[^,]*,[^,]*,[NS],[^,]*,[EW],[^,]*,[^,]*,[^,]*,([^,]*) ]]; then
    altitude=${BASH_REMATCH[1]}
else
    altitude=""
fi

# Write to CSV
echo "$timestamp,$latitude,$longitude,$altitude" >> "$OUTPUT"

echo "Logged: $timestamp, $latitude, $longitude, $altitude"
U-Blox AG [u-blox 7]
