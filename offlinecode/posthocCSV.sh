#!/bin/bash

workingDirectory=$1
startDate=$2

echo $workingDirectory $startDate

cd $workingDirectory

echo "Location,DeviceID,year,month,day,hour,minute" > $startDate.csv

### Cycle through the jpg files in the directory

for file in $(ls *.jpg); do
    ./getCSVentry.sh $file >> $startDate.csv
done

