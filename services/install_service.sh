#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/pi/iot-classroom"
SERVICE_NAME="iot-classroom.service"

if [[ ! -f "/services/" ]]; then
  echo "Service file not found in /services"
  exit 1
fi

echo "Copying service to /etc/systemd/system/"
sudo cp "/services/" /etc/systemd/system/

echo "Reloading systemd daemon"
sudo systemctl daemon-reload

echo "Enabling and starting "
sudo systemctl enable --now 

echo "Service installed"
