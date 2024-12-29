#!/bin/bash

# Find the container using the image "sigoden/dufs" 
CONTAINER_ID=$(docker ps --filter "ancestor=sigoden/dufs" -q)

if [ -n "$CONTAINER_ID" ]; then
    docker kill "$CONTAINER_ID"
else
    echo "No container found running 'sigoden/dufs'"
fi

