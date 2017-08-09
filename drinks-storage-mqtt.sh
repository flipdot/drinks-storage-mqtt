#!/bin/bash
# Execute $PY_SCRIPT if not already running
PY_SCRIPT='drinks-storage-mqtt.py'
pgrep -a python | grep "$PY_SCRIPT" || (cd "$(dirname $0)" && exec "./$PY_SCRIPT")
