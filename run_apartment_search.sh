#!/bin/bash

# Set working directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set up logging with timestamp
LOG_FILE="logs/apartment_search_$(date +\%Y\%m\%d).log"
mkdir -p logs

# Run the script and redirect both stdout and stderr to log file
python main.py >> "$LOG_FILE" 2>&1

# Add a separator line for better log readability
echo -e "\n----------------------------------------\n" >> "$LOG_FILE"

# Deactivate virtual environment
deactivate 