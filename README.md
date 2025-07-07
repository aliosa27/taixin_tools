# Taixin LibNetat Tool v2.0 
## Overview

The Taixin LibNetat Tool v2.0 is a cross-platform network analysis and AT command communication tool designed for interacting with Taixin wireless devices. This version features enhanced multiplatform support which is missing from the official tool and my implementation which sucked.

## Features

### Core Functionality
- **Device Discovery**: Automatic scanning and detection of devices on the network
- **AT Command Interface**: Send and receive AT commands to/from devices
- **Network Communication**: UDP-based packet transmission using Scapy library for cross platform compatibility(woot!)
- **Device Management**: Configuration loading, saving, and device information retrieval
- **Real-time Monitoring**: Live packet capture and response monitoring

### Multiplatform Support (v2.0)
- **Windows**: Full compatibility with Windows network interfaces
- **macOS**: Native support for macOS network stack
- **Linux**: Optimized for Linux distributions with proper interface handling
- **Auto-detection**: Automatic platform detection and interface selection

### User Interface Options
- **Command Line Interface**: Traditional CLI for scripting and automation
- **Enhanced UI**: Optional curses-based interactive interface (when available)
- **Debug Mode**: Comprehensive logging and debugging capabilities

### Network Features
- **Interface Management**: Automatic or manual network interface selection
- **Packet Capture**: Real-time packet monitoring with Scapy
- **Timeout Management**: Configurable scan and response timeouts

## Installation

### Prerequisites
```bash
# Install Python 3.6+ and pip
python3 --version
pip3 --version

# Install required dependencies
pip3 install scapy
```

### Optional Dependencies
```bash
# For enhanced UI (Linux/macOS)
pip3 install curses

# For command history (recommended)
pip3 install readline
```

### Platform-Specific Notes

#### Linux
```bash
# May require elevated privileges for raw packet access
sudo python3 libnetat.py --help
```

#### macOS
```bash
# Install Scapy with libpcap support
pip3 install scapy[complete]
```

#### Windows
```bash
# Install WinPcap or Npcap
# Download from: https://nmap.org/npcap/
pip3 install scapy
```

## Usage

### Basic Syntax
```bash
python3 libnetat.py [interface] [options]
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `interface` | Network interface to use ('auto' for automatic) | auto |
| `--command` | AT command to send or special command | None |
| `--dest_mac` | Target device MAC address | None |
| `--debug` | Enable debug output | False |
| `--scan-timeout` | Scan timeout in seconds | 8 |
| `--response-timeout` | Response timeout in seconds | 5 |
| `--enhanced` | Use enhanced curses UI | False |
| `--log-responses` | Enable response logging | False |
| `--log-file` | Log file path | responses.log |
| `--list-interfaces` | List available network interfaces | False |
| `--test-packet` | Send test packet | False |

### Common Usage Examples

#### 1. List Available Network Interfaces
```bash
python3 libnetat.py --list-interfaces
```
Output:
```
Available network interfaces (Scapy detected):
  1. eth0         - IP: 192.168.1.100, MAC: 00:11:22:33:44:55
  2. wlan0        - IP: 192.168.1.101, MAC: 00:11:22:33:44:66
  3. lo           - IP: 127.0.0.1, MAC: Unknown MAC

```

#### 2. Scan for Devices
```bash
# Auto-select interface and scan
python3 libnetat.py --command scan

# Use specific interface
python3 libnetat.py eth0 --command scan
```

#### 3. Send AT Commands
```bash

# Get device information
python3 libnetat.py eth0 --command deviceinfo

# Send command to specific device
python3 libnetat.py eth0 --dest_mac 00:11:22:33:44:55 --command "at+mode?"
```

#### 4. Configuration Management
```bash
# Save current device configuration
python3 libnetat.py eth0 --command "saveconfig backup.txt"

# Load configuration from file
python3 libnetat.py eth0 --command "loadconfig backup.txt"
```

#### 5. Interactive Mode
```bash
# Launch nCurses ui
python3 libnetat.py eth0 --enhanced

# Launch with debug mode
python3 libnetat.py eth0 --debug --enhanced
```

#### 6. Test Network Setup
```bash
# Test packet transmission
python3 libnetat.py eth0 --test-packet

```

## AT Commands

### Production Commands (Set)
The tool supports numerous production-level SET commands including:
- `mode`, `ssid`, `keymgmt`, `psk` - Basic wireless configuration
- `txpower`, `channel`, `freq_range` - RF parameters
- `beacon_int`, `dtim_period` - AP timing parameters
- `country_region`, `acs` - Regulatory and channel selection
- `pair`, `unpair`, `pairing` - Device pairing functions
- And many more...

### Production Commands (Get)
Query commands for retrieving device status:
- `mode`, `ssid`, `rssi`, `conn_state` - Connection status
- `sta_list`, `scan_list`, `bssid` - Network information
- `battery_level`, `temperature` - Device health
- `fwinfo`, `stainfo`, `signal` - System information

### Debug Commands
Advanced debugging and testing commands available in debug mode.

## Configuration Files

### Device Configuration Format
When using `saveconfig` or `loadconfig`, the tool creates/reads configuration files in a structured format containing device settings and parameters.

### Logging Configuration
The tool generates detailed logs in `netat_scapy.log` for troubleshooting and analysis.

## Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Solution: Run with elevated privileges
sudo python3 libnetat.py --command scan
```

#### 2. Scapy Import Error
```bash
# Solution: Install Scapy
pip3 install scapy

# For complete installation
pip3 install scapy[complete]
```

#### 3. No Network Interfaces Found
```bash
# Check available interfaces
python3 libnetat.py --list-interfaces

# Try with auto-detection
python3 libnetat.py auto --command scan
```

#### 4. No Devices Found
- Ensure devices are powered on and are on the same network segment
- Check network connectivity
- Verify correct network interface selection
- Try increasing scan timeout: `--scan-timeout 15`

#### 5. Packet Capture Issues
```bash
# Test packet transmission
python3 libnetat.py eth0 --test-packet

# Monitor with external tools
sudo tcpdump -i eth0 udp port 56789
```

### Debug Mode
Enable debug mode for detailed troubleshooting:
```bash
python3 libnetat.py eth0 --debug --command scan
```

Debug mode provides:
- Detailed packet information
- Network interface details
- Command execution traces
- Error stack traces

## Platform-Specific Features

### Windows
- Automatic WinPcap/Npcap detection
- Windows-specific network interface handling
- UAC prompt handling for elevated privileges

### macOS
- Native macOS network stack integration
- Automatic interface selection optimization which is broken so specify an interface
- macOS-specific packet capture handling

### Linux
- Optimized for various Linux distributions
- Enhanced interface detection
- Proper raw socket handling

## Advanced Usage

### Scripting Integration
The tool can be integrated into automated scripts:
```bash
#!/bin/bash
# Automated device scanning and configuration

# Scan for devices
python3 libnetat.py eth0 --command scan > devices.txt

# Configure found devices
python3 libnetat.py eth0 --command "loadconfig production.txt"
```

### Response Logging
Enable comprehensive response logging:
```bash
python3 libnetat.py eth0 --log-responses --log-file device_responses.log --command deviceinfo
```

## Security Considerations

- The tool requires raw packet access which may need elevated privileges
- Network communication is unencrypted - use on trusted networks only
- Configuration files may contain sensitive information - protect accordingly
- Debug logs may contain network traffic details - review before sharing

## Version History

### v2.0 Features
- Enhanced multiplatform support (Windows, macOS, Linux)
- Improved network interface detection and handling
- Optimized packet capture and transmission
- Better error handling and user feedback
- Enhanced debugging capabilities
- Improved configuration management

## Support and Updates

- **Repository**: https://github.com/aliosa27/taixin_tools
- **Contact**: aliosa27@aliosa27.me
- **Issues**: Report bugs and feature requests on GitHub

## License

This tool is provided as-is for device management purposes. Use responsibly kids.

---

*Taixin LibNetat Tool v2.0 - Cross-Platform Network Analysis Tool*


server.py is a python web based wrapper for hgpriv with basic support for libnetat.

 it expects that hgpriv or libnetat are compiled and installed in /sbin.
 The mode can be switched in /etc/mode.conf or via the web gui on the system page.

You will need to compile my version of libnetat, it adds support to run at commands from the command line, device switching, scanning, and supports running commands on remote devices by passing a mac address on the command line. 

libnetat support is basic, rssi/connection status/etc work. 
 site survey does not work in this mode yet but that seems to be a firmware issue.
 
 sever.py expects that you have copied the config files over to /etc
 it also expects that you leave the interface at its default name of hg0(will change this in the future)

By default the driver loads /etc/hgcif.conf when loaded. You will need to make sure you load the driver on boot
 

 It exposes all of the get and set commands that hgpriv supports. in additon, it will create the /etc/hgicf.conf file which 
 the driver loads on load. 

 It supports upgrading firmware via the ota interface the driver exposes. 
 

theres a bunch of other stuff here, there is an rssi graph which was the reason i started this in the first place, when testing out the usb based modules.

copy the configs in etc to etc on your host. 


python server.py 
and you should be good to go!
