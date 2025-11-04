#!/usr/bin/env python3
"""
Silent wrapper for libnetat.py - suppresses verbose output and errors
Returns only the actual command response
"""

import sys
import os
import io
import contextlib

# Add path for libnetat
sys.path.insert(0, '/usr/lib/taixintools')

# Redirect stderr to suppress libpcap warnings and other noise
sys.stderr = open(os.devnull, 'w')

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Now import libnetat after stderr is redirected
from libnetat import *

def main():
    """Main function that captures and filters output"""

    # Capture stdout
    captured_output = io.StringIO()

    # Run the original main with captured output
    with contextlib.redirect_stdout(captured_output):
        try:
            # Get arguments (skip script name)
            args = sys.argv[1:]

            # Parse arguments manually for our wrapper
            interface = None
            command = None
            dest_mac = None
            scan_timeout = 3
            response_timeout = 3

            i = 0
            while i < len(args):
                arg = args[i]
                if arg.startswith('--'):
                    if arg == '--command' and i + 1 < len(args):
                        command = args[i + 1]
                        i += 2
                    elif arg == '--dest_mac' and i + 1 < len(args):
                        dest_mac = args[i + 1]
                        i += 2
                    elif arg == '--scan-timeout' and i + 1 < len(args):
                        scan_timeout = float(args[i + 1])
                        i += 2
                    elif arg == '--response-timeout' and i + 1 < len(args):
                        response_timeout = float(args[i + 1])
                        i += 2
                    else:
                        i += 1
                else:
                    if interface is None:
                        interface = arg
                    i += 1

            if not interface:
                print("Error: Interface required", file=sys.__stderr__)
                sys.exit(1)

            # Call the main function
            from libnetat import main as libnetat_main
            libnetat_main(
                ifname=interface,
                command=command,
                dest_mac=dest_mac,
                debug=False,
                scan_timeout=scan_timeout,
                response_timeout=response_timeout,
                enhanced_ui=False,
                log_responses=False
            )

        except SystemExit:
            pass
        except Exception as e:
            # Silently ignore most errors
            pass

    # Get the captured output
    output = captured_output.getvalue()

    # Filter output to show only relevant lines
    lines = output.split('\n')
    filtered_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip header/banner lines
        if 'Taixin' in line or '=====' in line or 'Updates at' in line or '@' in line:
            continue
        # Skip status lines
        if line.startswith('Sending command:') or line.startswith('Response timeout:'):
            continue
        if line.startswith('Scanning for') or line.startswith('Interface:') or line.startswith('Broadcast to:'):
            continue
        if line.startswith('Scan timeout:') or line.startswith('Waiting for'):
            continue
        # Skip found device header but keep the device list
        if line.startswith('Found') and 'device(s)' in line:
            continue

        # Keep response lines and device MAC addresses
        if line.startswith('Response:') or line.startswith('No response'):
            filtered_lines.append(line)
        elif ':' in line and len(line.split(':')) >= 6:  # MAC address format
            filtered_lines.append(line)
        elif line and not line.startswith('ERROR:'):  # Keep other meaningful lines except errors
            filtered_lines.append(line)

    # Print filtered output to real stdout
    for line in filtered_lines:
        print(line, file=sys.__stdout__)

if __name__ == "__main__":
    main()
