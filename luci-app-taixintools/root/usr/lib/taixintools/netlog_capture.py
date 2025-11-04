#!/usr/bin/env python3
"""
NetLog capture wrapper for LuCI
Starts netlog capture and outputs to stdout
"""

import sys
import os
import signal
import time

# Add parent directory to path to import libnetat
sys.path.insert(0, '/usr/lib/taixintools')

try:
    from libnetat import ScapyNetAtMgr
except ImportError as e:
    print(f"Error: Could not import libnetat: {e}", file=sys.stderr)
    sys.exit(1)

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\nStopping netlog capture...", file=sys.stderr)
    sys.exit(0)

def main():
    if len(sys.argv) < 3:
        print("Usage: netlog_capture.py <interface> <device_mac>", file=sys.stderr)
        sys.exit(1)

    interface = sys.argv[1]
    device_mac = sys.argv[2]

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Define display callback to output logs in real-time
    def display_callback(log_line):
        """Callback to display netlog output"""
        print(log_line, flush=True)

    try:
        # Initialize manager
        mgr = ScapyNetAtMgr(interface, debug=False)

        # Parse MAC address
        from libnetat import parse_mac_address
        device_bytes = parse_mac_address(device_mac)
        mgr.dest = device_bytes

        # Set display callback before starting netlog
        mgr.netlog_display_callback = display_callback

        # Start packet capture
        mgr.start_packet_capture()

        # Start netlog with specific device MAC
        if not mgr.start_netlog(specific_mac=device_bytes):
            print("Failed to start netlog", flush=True)
            sys.exit(1)

        print(f"NetLog started on interface {interface} for device {device_mac}", flush=True)
        print("Listening for NetLog packets...", flush=True)

        # Keep running - the callback will output data as it arrives
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping netlog capture...", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        if 'mgr' in locals():
            mgr.stop_netlog()
            mgr.stop_packet_capture()

if __name__ == "__main__":
    main()
