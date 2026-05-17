#!/usr/bin/env bash

VENV_PATH="/home/daniel/wetter_rx_script/recieverscript/venv"
PYTHON_SCRIPT="/home/daniel/wetter_rx_script/recieverscript/weather_receiver.py"

source "$VENV_PATH/bin/activate"

while true
do
  rtl_433 -d :00000999 -R 32 -F json | python -u "$PYTHON_SCRIPT"
  echo "[WARN] rtl_433 oder Python wurde beendet. Neustart in 10 Sekunden..."
  sleep 10
done
