#!/bin/bash

sleep 5

/home/canopylife/bin/checkMode.py
status=$?

if [ $status = 1 ]; then
    timeout 3 /home/arducam/bin/statusBlinker.py 2; 
    /home/arducam/bin/statusBlinker.py 6
    sleep 1
    /home/arducam/bin/statusBlinker.py 6
    /home/arducam/bin/webInterface.py
else
    echo "In power saver mode."
    timeout 3 /home/arducam/bin/statusBlinker.py 1; 
    /home/arducam/bin/statusBlinker.py 6
    sleep 1
    /home/arducam/bin/statusBlinker.py 6
fi

