# This script is used to show all environments in the cloudshare service.
# It requires the mxcloudshare.py script to be in the same directory.
#!/bin/bash
# Check if the mxcloudshare.py script exists
if [ ! -f "./mxcloudshare.py" ]; then
    echo "Error: mxcloudshare.py script not found in the current directory."
    exit 1
fi

#./mxcloudshare.py --loglevel debug --outformat table --keyfile ./cloudshare.keys env-show-all
./mxcloudshare.py --outformat table --keyfile ./cloudshare.keys env-show-all
