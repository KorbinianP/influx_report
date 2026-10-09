#!/bin/bash
#set -ex
#exec 1>/var/log/openhab/executable_script.log 2>&1  # OpenHAB should have write access here
#cd /var/lib/openhab/influx_report
#source .venv/bin/activate
#rm -f *.png || true
#python main.py


set -x  # Keep debug output
echo "Script started: $(date)" >> /tmp/openhab_debug.log 2>&1
exec 1>/var/log/openhab/executable_script.log 2>&1
echo "Script started at $(date)"
echo "Current directory: $(pwd)"
cd /var/lib/openhab/influx_report || { echo "CD failed"; exit 1; }
echo "Changed to: $(pwd)"
ls -la .venv/bin/activate || { echo "venv activate not found"; exit 1; }
source .venv/bin/activate || { echo "Activation failed"; exit 1; }
echo "Python: $(which python)"
echo "Removing PNGs..."
rm -f *.png 2>/dev/null || true
echo "Running main.py..."
python main.py
echo "Script completed at $(date)"
