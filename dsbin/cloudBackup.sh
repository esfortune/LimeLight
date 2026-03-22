#!/bin/bash
# Copyright Eric Fortune, CanopyLife, March 2026
# Code written for MothPad device.
#
# Backs up the most recent completed Jotta folder to rclone cloud storage.
# Intended to run via cron after midnight.
#
# Logic: running after midnight on the 21st, we back up the 19th (or the most
# recent folder before that). We skip the 20th because it may still be
# receiving data from dailyBackup.sh.  "Most recent before yesterday midnight"
# means any folder last modified on the 19th or earlier.

#########################################################################
## CONFIG

SERIAL=$(cat /home/canopylife/serialNumber.txt | tr -d '[:space:]')
JOTTA_DIR=$(grep backup_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p")
REMOTE="CanopyLife:MothPadData"

#########################################################################
## FIND TARGET FOLDER
# We want the most recently modified folder that was last modified
# before yesterday's midnight (i.e., completed 2+ days ago).

YESTERDAY_MIDNIGHT=$(date -d "yesterday 00:00:00" +%s)

TARGET=""
while IFS= read -r dir; do
    dir_mtime=$(stat -c %Y "$dir")
    if [ "$dir_mtime" -lt "$YESTERDAY_MIDNIGHT" ]; then
        TARGET="$dir"
        break
    fi
done < <(find "$JOTTA_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -rn | awk '{print $2}')

if [ -z "$TARGET" ]; then
    echo "[cloudBackup] No completed folder found (2+ days old) in $JOTTA_DIR"
    exit 1
fi

FOLDER_NAME=$(basename "$TARGET")
DEST="$REMOTE/$SERIAL/$FOLDER_NAME"

#########################################################################
## RUN RCLONE

echo "[cloudBackup] Backing up: $TARGET"
echo "[cloudBackup] Destination: $DEST"

rclone copy "$TARGET" "$DEST" --log-level INFO

if [ $? -eq 0 ]; then
    echo "[cloudBackup] Success: $FOLDER_NAME backed up to $DEST"
else
    echo "[cloudBackup] ERROR: rclone failed for $FOLDER_NAME"
    exit 1
fi
