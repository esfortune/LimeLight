#!/bin/bash

sleep 5

/home/canopylife/bin/checkMode.py
status=$?

if [ $status = 1 ]; then
    timeout 3 /home/canopylife/bin/statusBlinker.py 2; 
    /home/canopylife/bin/statusBlinker.py 6
    sleep 1
    /home/canopylife/bin/statusBlinker.py 6
    /home/canopylife/bin/webInterface.py
else
    echo "In power saver mode."
    timeout 3 /home/canopylife/bin/statusBlinker.py 1; 
    /home/canopylife/bin/statusBlinker.py 6
    sleep 1
    /home/canopylife/bin/statusBlinker.py 6
fi

