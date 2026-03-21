#!/bin/bash
# Copyright Eric Fortune, CanopyLife, March 2026
# Code written for MothPad device.
#
# Weekly full sync: backs up every folder in the Jotta directory to cloud.
# Runs at most 2 rclone instances concurrently to avoid overwhelming the
# connection or the device.  rclone skips unchanged files, so re-running
# this is safe and efficient.

#########################################################################
## CONFIG

SERIAL=$(cat /home/canopylife/serialNumber.txt | tr -d '[:space:]')
JOTTA_DIR=$(grep backup_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p")
REMOTE="CanopyLife:MothPadData"
MAX_JOBS=2

#########################################################################
## FIND ALL FOLDERS

mapfile -t FOLDERS < <(find "$JOTTA_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

if [ ${#FOLDERS[@]} -eq 0 ]; then
    echo "[cloudBackupFull] No folders found in $JOTTA_DIR"
    exit 0
fi

echo "[cloudBackupFull] Found ${#FOLDERS[@]} folder(s) to sync"

#########################################################################
## SYNC WITH CONCURRENCY LIMIT

PIDS=()

for dir in "${FOLDERS[@]}"; do
    FOLDER_NAME=$(basename "$dir")
    DEST="$REMOTE/$SERIAL/$FOLDER_NAME"

    echo "[cloudBackupFull] Starting: $FOLDER_NAME -> $DEST"
    rclone copy "$dir" "$DEST" --log-level INFO &
    PIDS+=($!)

    # If we've reached MAX_JOBS, wait for one to finish before continuing
    while [ ${#PIDS[@]} -ge $MAX_JOBS ]; do
        NEW_PIDS=()
        for pid in "${PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                NEW_PIDS+=("$pid")
            fi
        done
        PIDS=("${NEW_PIDS[@]}")
        [ ${#PIDS[@]} -ge $MAX_JOBS ] && sleep 5
    done
done

# Wait for any remaining background jobs
for pid in "${PIDS[@]}"; do
    wait "$pid"
done

echo "[cloudBackupFull] All folders synced."
