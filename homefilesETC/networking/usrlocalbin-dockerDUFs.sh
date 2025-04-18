#!/bin/bash

# Path to the data directory
DATA_DIR="/home/arducam/data"

# Check the state of GPIO 23 using pinctrl
PIN_STATE=$(pinctrl lev 23)

if [ "$PIN_STATE" = "1" ]; then
  echo "[✓] GPIO 23 is HIGH — launching Docker server..."
  docker run -d -v "$DATA_DIR":/data -p 5000:5000 --rm sigoden/dufs /data -A
else
  echo "[!] GPIO 23 is LOW — skipping Docker server launch."
fi

