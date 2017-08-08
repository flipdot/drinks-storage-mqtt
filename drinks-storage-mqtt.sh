#!/bin/bash
# Execute $PY_SCRIPT if not already running
PY_SCRIPT='drinks-storage-mqtt.py'
pgrep -a python | grep "$PY_SCRIPT" || exec "$(dirname $0)/$PY_SCRIPT"
