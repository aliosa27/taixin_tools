#!/bin/sh

# netlog_read.sh - Read NetLog output

LOG_FILE="/tmp/taixintools_netlog.log"

if [ ! -f "$LOG_FILE" ]; then
    echo ""
    exit 0
fi

# Return the last 100 lines of the log
tail -n 100 "$LOG_FILE"
