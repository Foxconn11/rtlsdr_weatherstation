#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_PATH="$SCRIPT_DIR/.#venv"
PYTHON_SCRIPT="$SCRIPT_DIR/weather_receiver.py"

source "$VENV_PATH/bin/activate"

while true
do
  rtl_433 -d :00000999 -R 32 -F json | python -u "$PYTHON_SCRIPT"
  echo "[WARN] rtl_433 oder Python wurde beendet. Neustart in 10 Sekunden..."
  sleep 10
done
