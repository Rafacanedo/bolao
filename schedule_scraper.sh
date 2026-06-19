#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Go to project directory
cd /home/rafa/Projects/bolao

# Get target run time (e.g. 12:00)
TARGET_TIME=$(./.venv/bin/python odds_scraper.py --print-time)
echo "Target run time for today's odds scraper: $TARGET_TIME"

# Current time and target time in seconds
CURRENT_SECS=$(date +%s)
TARGET_SECS=$(date -d "$TARGET_TIME" +%s 2>/dev/null || date -d "today $TARGET_TIME" +%s 2>/dev/null)

if [ -z "$TARGET_SECS" ]; then
    echo "Failed to parse target time. Running immediately as fallback."
    ./.venv/bin/python odds_scraper.py
    ./.venv/bin/python world_cup_manager.py --tune
    ./.venv/bin/python world_cup_manager.py
    ./.venv/bin/python world_cup_manager.py --submit-sp || echo "Skipping ScorePick submission fallback"
    exit 0
fi

# If target time is in the past (or within the next 60 seconds), run now
DIFF=$((TARGET_SECS - CURRENT_SECS))
if [ $DIFF -le 0 ]; then
    echo "Target time has already passed or is right now. Running immediately..."
    ./.venv/bin/python odds_scraper.py
    ./.venv/bin/python world_cup_manager.py --tune
    ./.venv/bin/python world_cup_manager.py
    ./.venv/bin/python world_cup_manager.py --submit-sp || echo "Skipping ScorePick submission"
else
    echo "Target time is in the future. Sleeping for $DIFF seconds ($((DIFF/60)) minutes) before running..."
    sleep $DIFF
    
    echo "Running daily automation routine..."
    ./.venv/bin/python odds_scraper.py
    ./.venv/bin/python world_cup_manager.py --tune
    ./.venv/bin/python world_cup_manager.py
    ./.venv/bin/python world_cup_manager.py --submit-sp || echo "Skipping ScorePick submission"
fi
