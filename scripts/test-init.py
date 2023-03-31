import os
import sys
from urllib.request import urlretrieve

# URL of the CSV file to download
url = "https://kanaries-app.s3.ap-northeast-1.amazonaws.com/public-datasets/bike_sharing_dc.csv"

# Directory to download the file to
dir = "./tests"

# Create the directory if it doesn't exist
os.makedirs(dir, exist_ok=True)

# Download the file using urlretrieve
try:
    urlretrieve(url, f"{dir}/bike_sharing_dc.csv")
except Exception as e:
    print(f"Error: could not download the file\n{e}", file=sys.stderr)
    sys.exit(1)