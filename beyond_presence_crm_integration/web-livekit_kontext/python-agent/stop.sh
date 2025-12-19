#!/bin/bash

echo "Stopping Python agent..."



# Kill all related processes
pkill -f "python.*agent.py" 2>/dev/null
pkill -f "uv.*agent.py" 2>/dev/null
pkill -f "livekit.*agent" 2>/dev/null
pkill -f "multiprocessing.*spawn" 2>/dev/null

# Wait a moment
sleep 1

# Force kill if still running
pkill -9 -f "python.*agent.py" 2>/dev/null
pkill -9 -f "uv.*agent.py" 2>/dev/null
pkill -9 -f "livekit.*agent" 2>/dev/null
pkill -9 -f "multiprocessing.*spawn" 2>/dev/null

echo "Python agent stopped."

# Check if any processes are still running
remaining=$(ps aux | grep -E "python.*agent|uv.*agent" | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "Warning: $remaining agent process(es) may still be running"
    echo "Run 'ps aux | grep agent' to check"
fi