#!/bin/bash

# URL of the CSV file to download
url="https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv"

# Directory to download the file to
dir="./tests"

# Create the directory if it doesn't exist
mkdir -p "$dir"

# Download the file using curl
if command -v curl >/dev/null; then
    curl "$url" -o "$dir/bike_sharing_dc.csv"
elif command -v wget >/dev/null; then
    wget "$url" -O "$dir/bike_sharing_dc.csv"
else
    echo "Error: could not find curl or wget to download the file" >&2
    exit 1
fi