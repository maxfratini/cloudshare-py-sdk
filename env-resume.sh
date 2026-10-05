#!/bin/bash
# Resume a suspended environment in the CloudShare service.
#
# Requires the `mxcloudshare` CLI on PATH (uv run --project . / uv tool install /
# or the compiled binary in dist/). Credentials come from ./cloudshare.keys or
# from CLOUDSHARE_API_ID / CLOUDSHARE_API_KEY in the environment.
#
# Note: cyclopts wants the command name BEFORE the options, i.e.
#   mxcloudshare env-resume --envid ID --outformat table
set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Resume a suspended environment in the cloudshare service."
    echo "Usage: $0 <environment_id>"
    exit 1
fi

exec mxcloudshare env-resume --envid "$1" \
    --outformat table \
    --keyfile ./cloudshare.keys \
    "${@:2}"