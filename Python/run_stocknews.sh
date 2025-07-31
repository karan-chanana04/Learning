#!/bin/bash

# Stock News Automation Script
# This script runs the Python stock news program

# Set the path to your Python environment (adjust as needed)
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9"
SCRIPT_PATH="/Users/karanchanana/stocknews.py"
LOG_PATH="/Users/karanchanana/stocknews.log"

# Change to the script directory
cd /Users/karanchanana

# Add timestamp to log
echo "===========================================" >> "$LOG_PATH"
echo "Stock News Script Started: $(date)" >> "$LOG_PATH"

# Run the Python script and capture output
$PYTHON_PATH "$SCRIPT_PATH" >> "$LOG_PATH" 2>&1

# Add completion timestamp
echo "Stock News Script Completed: $(date)" >> "$LOG_PATH"
echo "===========================================" >> "$LOG_PATH"
echo "" >> "$LOG_PATH"
