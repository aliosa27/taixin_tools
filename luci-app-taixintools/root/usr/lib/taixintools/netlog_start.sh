#!/bin/sh

# netlog_start.sh - Start NetLog capture
# Usage: netlog_start.sh <interface> <device_mac>

INTERFACE="$1"
DEVICE="$2"

if [ -z "$INTERFACE" ]; then
    echo "Error: Interface is required"
    exit 1
fi

if [ -z "$DEVICE" ]; then
    echo "Error: Device MAC is required"
    exit 1
fi

NETLOG_CAPTURE="/usr/lib/taixintools/netlog_capture.py"
PID_FILE="/var/run/taixintools_netlog.pid"
LOG_FILE="/tmp/taixintools_netlog.log"

if [ ! -f "$NETLOG_CAPTURE" ]; then
    echo "Error: netlog_capture.py not found at $NETLOG_CAPTURE"
    exit 1
fi

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps | grep -q "^[[:space:]]*$OLD_PID "; then
        echo "NetLog is already running (PID: $OLD_PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Clear the log file
> "$LOG_FILE"

# Start netlog capture in background with device MAC
# -u flag disables Python buffering for real-time output
nohup python3 -u "$NETLOG_CAPTURE" "$INTERFACE" "$DEVICE" > "$LOG_FILE" 2>&1 &
PID=$!

echo $PID > "$PID_FILE"
echo "NetLog started on interface $INTERFACE for device $DEVICE (PID: $PID)"
