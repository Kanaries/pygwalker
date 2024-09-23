#!/bin/bash

# URL of the CSV file to download
url="https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv"

# Directory to download the file to
dir="./tests"

# Create the directory if it doesn't exist
mkdir -p "$dir" || {
    echo "Error: could not create directory '$dir'" >&2
    exit 1
}

# Download the file using curl
if command -v curl >/dev/null; then
    curl -f "$url" -o "$dir/bike_sharing_dc.csv" || {
        echo "Error: could not download file from '$url'" >&2
        exit 1
    }
elif command -v wget >/dev/null; then
    wget -q --show-progress "$url" -O "$dir/bike_sharing_dc.csv" || {
        echo "Error: could not download file from '$url'" >&2
        exit 1
    }
else
    echo "Error: could not find curl or wget to download the file" >&2
    exit 1
fi

# Check if the file was downloaded successfully
if [ ! -f "$dir/bike_sharing_dc.csv" ]; then
    echo "Error: file '$dir/bike_sharing_dc.csv' was not downloaded successfully" >&2
    exit 1
fi
