#!/bin/sh

# netat_scan.sh - Scan for NetAT devices
# Usage: netat_scan.sh <interface>

INTERFACE="$1"

if [ -z "$INTERFACE" ]; then
    echo "Error: Interface is required"
    exit 1
fi

LIBNETAT="/usr/lib/taixintools/libnetat.py"

if [ ! -f "$LIBNETAT" ]; then
    echo "Error: libnetat.py not found at $LIBNETAT"
    exit 1
fi

# Execute scan and return device list
# Use silent wrapper to suppress verbose output
SILENT_WRAPPER="/usr/lib/taixintools/libnetat_silent.py"
if [ -f "$SILENT_WRAPPER" ]; then
    python3 "$SILENT_WRAPPER" "$INTERFACE" --command scan --scan-timeout 5 2>&1
else
    python3 "$LIBNETAT" "$INTERFACE" --command scan --scan-timeout 5 2>&1
fi
