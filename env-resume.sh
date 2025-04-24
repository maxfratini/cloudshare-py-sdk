# This script is used to resume a suspended environment in the cloudshare service.
# It requires the mxcloudshare.py script to be in the same directory.
#!/bin/bash
# Check if the mxcloudshare.py script exists
if [ ! -f "./mxcloudshare.py" ]; then
    echo "Error: mxcloudshare.py script not found in the current directory."
    exit 1
fi
# Check if the user provided an environment ID
if [ -z "$1" ]; then
    echo "Resume a suspended environment in the cloudshare service."
    echo "Usage: $0 <environment_id>"
    exit 1
fi
#./mxcloudshare.py --loglevel debug --outformat table --keyfile ./cloudshare.keys env-resume --envid "$1"
./mxcloudshare.py --outformat table --keyfile ./cloudshare.keys env-resume --envid "$1"
