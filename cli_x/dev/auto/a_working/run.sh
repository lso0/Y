#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Clear the log file
> requests.log

# Start mitmproxy in the background
mitmdump -s mitm_script.py --listen-host 127.0.0.1 --listen-port 8080 &
MITM_PID=$!

# Wait a moment for mitmproxy to start
sleep 2

# Check if mitmproxy is running
if ! ps -p $MITM_PID > /dev/null; then
    echo "Error: mitmproxy failed to start"
    exit 1
fi

echo "mitmproxy is running on 127.0.0.1:8080"

# Run the browser automation
python browser_script.py

# Cleanup
kill $MITM_PID 