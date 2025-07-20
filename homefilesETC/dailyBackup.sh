#!/bin/bash
# Copyright Eric Fortune, CanopyLife, June 2025
# Code written for Mothpad device.

#########################################################################
## SET VARIABLES

dataDIR=`grep data_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`

numPics=`clImages.sh | sed 's/[^0-9]*//g'`

echo $dataDIR $numPics

if [ "$numPics" -gt "1" ]; then

    # cd into the data directory
    cd $dataDIR/Studio

    # Get the first filname
    earliestFile=`ls -t *.jpg | tail -1`

    # Convert to datestamp ########################################

    # Extract the year and MMDD using parameter expansion and cut
    year=$(echo "$earliestFile" | cut -d'_' -f3)
    mmdd=$(echo "$earliestFile" | cut -d'_' -f4 | cut -c1-4)

    # Extract month and day
    month=${mmdd:0:2}
    day=${mmdd:2:2}

    case $month in
      01) month_abbr="Jan" ;;
      02) month_abbr="Feb" ;;
      03) month_abbr="Mar" ;;
      04) month_abbr="Apr" ;;
      05) month_abbr="May" ;;
      06) month_abbr="Jun" ;;
      07) month_abbr="Jul" ;;
      08) month_abbr="Aug" ;;
      09) month_abbr="Sep" ;;
      10) month_abbr="Oct" ;;
      11) month_abbr="Nov" ;;
      12) month_abbr="Dec" ;;
      *)  month_abbr="Err" ;;
    esac

    # Compose datestamp
    datestamp="${year}${month_abbr}${day}"

echo $datestamp

    # And now we have our datestamp ###############################

    # This is our backup path from config.py with the current date
    backupDIR=`grep backup_path /home/canopylife/bin/config.py | sed -n "s/^.*'\(.*\)'.*$/\1/p"`/$datestamp

echo $backupDIR

    if [ -d "$dataDIR" ]; then
       # Directory the data directory exists, we can move forward

       if [ ! -d "$backupDIR" ]; then
          # If backup directory doesn't exist, then make it
          mkdir -p "$backupDIR"
       fi

       # move the directories
       mv $dataDIR/Studio $backupDIR/
       mv $dataDIR/*.txt $backupDIR/
       mv $dataDIR/*.csv $backupDIR/
       if [ -d "$dataDIR/Audio" ]; then
            mv $dataDIR/Audio $backupDIR/
       fi

    fi

fi

######################################################################################
## Check to see the position of the switch. If it is 1, then we are in "standard" mode
## and we should make the timelapse movie.

/home/canopylife/bin/checkMode.py
status=$?

if [ $status = 1 ]; then

   # Make the movie
   movieMaker.sh $backupDIR

fi
