#!/bin/sh

# netlog_stop.sh - Stop NetLog capture

PID_FILE="/var/run/taixintools_netlog.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "NetLog is not running"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps | grep -q "^[[:space:]]*$PID "; then
    kill $PID
    sleep 1
    # Force kill if still running
    if ps | grep -q "^[[:space:]]*$PID "; then
        kill -9 $PID
    fi
    echo "NetLog stopped (PID: $PID)"
else
    echo "NetLog process not found (stale PID file)"
fi

rm -f "$PID_FILE"
