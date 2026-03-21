#!/bin/bash

sleep 5

timeout 3 /home/canopylife/bin/statusBlinker.py 2
/home/canopylife/bin/statusBlinker.py 6
sleep 1
/home/canopylife/bin/statusBlinker.py 6
/home/canopylife/bin/webInterface.py

