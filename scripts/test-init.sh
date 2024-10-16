#!/usr/bin/env bash

set -e  # Exit immediately if a command exits with a non-zero status.

# URL of the CSV file to download
url="https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv"

# Directory to download the file to
dir="./tests"

# Filename to download
filename="bike_sharing_dc.csv"

# Create the directory if it doesn't exist
mkdir -p "$dir"

# Check available space in the target directory
available_space=$(df -h --output=avail "$dir" | awk '{print $1}')
required_space=$(curl -s -I "$url" | awk '/Content-Length/{print $2}' | numfmt --to=iec)
if [ "$available_space" -lt "$required_space" ]; then
    echo "Error: not enough available space in '$dir' to download the file" >&2
    exit 1
fi

# Download the file using curl or wget
if command -v curl >/dev/null; then
    echo "Using curl to download the file..."
    curl -s -f "$url" -o "$dir/$filename"
elif command -v wget >/dev/null; then
    echo "Using wget to download the file..."
    wget -q --show-progress "$url" -O "$dir/$filename"
else
    echo "Error: could not find curl or wget to download the file" >&2
    exit 1
fi

# Check if the file was downloaded successfully
if [ ! -f "$dir/$filename" ]; then
    echo "Error: file '$dir/$filename' was not downloaded successfully" >&2
    exit 1
else
    echo "File downloaded successfully: '$dir/$filename'"
fi

# Remove the file on error
trap 'rm -f "$dir/$filename"' ERR
