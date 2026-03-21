#!/bin/bash

# Path to the data directory
DATA_DIR="/home/canopylife/data"

echo "[✓] Launching Docker file server..."
docker run -d -v "$DATA_DIR":/data -p 5000:5000 --rm sigoden/dufs /data -A

