#!/bin/sh

# netat_send.sh - Send NetAT command via libnetat
# Usage: netat_send.sh <interface> <device_mac> <command>

INTERFACE="$1"
DEVICE="$2"
COMMAND="$3"

if [ -z "$INTERFACE" ] || [ -z "$DEVICE" ] || [ -z "$COMMAND" ]; then
    echo "Error: Interface, device MAC, and command are required"
    exit 1
fi

# Check if libnetat.py exists
LIBNETAT="/usr/lib/taixintools/libnetat.py"
if [ ! -f "$LIBNETAT" ]; then
    echo "Error: libnetat.py not found at $LIBNETAT"
    exit 1
fi

# Execute the NetAT command
# Use silent wrapper to suppress verbose output
SILENT_WRAPPER="/usr/lib/taixintools/libnetat_silent.py"
if [ -f "$SILENT_WRAPPER" ]; then
    python3 "$SILENT_WRAPPER" "$INTERFACE" --dest_mac "$DEVICE" --command "$COMMAND" --response-timeout 3 2>&1
else
    python3 "$LIBNETAT" "$INTERFACE" --dest_mac "$DEVICE" --command "$COMMAND" --response-timeout 3 2>&1
fi
