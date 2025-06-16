#!/bin/bash

X=`ps axu | grep -c rclone`
X=$((X - 1))

echo "rclone processes running:" $X
