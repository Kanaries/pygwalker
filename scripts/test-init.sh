#!/bin/bash

# URL of the CSV file to download
url="https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv"

# Directory to download the file to
dir="./tests"

# Create the directory if it doesn't exist
mkdir -p $dir

# Download the file using curl
curl $url -o "$dir/bike_sharing_dc.csv"
