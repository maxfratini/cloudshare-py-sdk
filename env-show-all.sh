#!/bin/bash
# Show all environments in the CloudShare service.
#
# Requires the `mxcloudshare` CLI on PATH (uv run --project . / uv tool install /
# or the compiled binary in dist/). Credentials come from ./cloudshare.keys or
# from CLOUDSHARE_API_ID / CLOUDSHARE_API_KEY in the environment.
#
# Note: cyclopts wants the command name BEFORE the options, i.e.
#   mxcloudshare env-show-all --outformat table
set -euo pipefail

exec mxcloudshare env-show-all \
    --outformat table \
    --tablewidth 120 \
    --keyfile ./cloudshare.keys \
    "$@"