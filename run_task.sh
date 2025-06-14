#!/bin/bash
# Description: This script runs a Docker Compose command to build and start services for a PV forecast application.
# Usage: ./run_task.sh
# Ensure the script is run from the correct directory
# Ensure the script is executable: chmod +x run_task.sh
# To run this script periodically, you can set up a cron job.
# 10 0,6,12,15 * * * /home/tero/services/pv-forecast/run_task.sh >> /home/tero/services/pv-forecast/cron.log 2>&1


set -e  # stop on error

cd /home/tero/services/pv-forecast
docker compose up --build --abort-on-container-exit
docker compose logs --no-color >> pv-forecast.log
docker compose down
