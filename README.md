
# Taixin tools Documentation

## Overview
The `libnetat.py` script provides tools to manage network devices using the NETAT protocol. It supports device discovery, command execution, and configuration management with logging capabilities.

---

## Usage

```bash
python libnetat.py <interface> [OPTIONS]
```

---

## Command-Line Options

| Option           | Description                                                                                      | Example                                   |
|-------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------|
| `<interface>`     | **Required**. The network interface to use.                                                     | `eth0`                                    |
| `--command`       | Specify a command to send to devices.                                                           | `--command "AT+SSID"`                      |
| `--dest_mac`      | Specify the destination MAC address for sending commands.                                       | `--dest_mac AA:BB:CC:DD:EE:FF`            |
| `--config_file`   | Load commands from a configuration file and send them to the destination device.                | `--config_file config.txt`                |
| `--logfile`       | Set the destination log file for output (default: `netat_mgr.log`).                             | `--logfile custom_log.log`                |

---

## Commands

### Non-Interactive Commands
These commands are executed directly using the `--command` option.

| Command    | Description                                                                                  | Example                     |
|------------|----------------------------------------------------------------------------------------------|-----------------------------|
| `netlog`   | Perform a NETLOG discovery(Not working yet) network.                                   | `python libnetat.py eth0 --command netlog` |
| `scan`     | Scan for available devices and display their MAC addresses.                                  | `python libnetat.py eth0 --command scan`  |
| `AT+<CMD>` | Send an AT command to the selected device. Replace `<CMD>` with the specific AT command.     | `python libnetat.py eth0 --command "AT+SSID"` |

---

### Interactive Mode Commands
Interactive mode starts when the script is run without specifying a `--command`. Users can input commands interactively.

| Command       | Description                                                                                     | Example                          |
|---------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `exit`        | Exit the interactive session.                                                                   | `exit`                           |
| `scan`        | Scan for available devices and display their MAC addresses.                                     | `scan`                           |
| `device`      | Display the currently selected destination MAC address.                                         | `device`                         |
| `at+cmd`    | Send an AT command to the currently selected device. Replace `<cmd>` with the AT command.       | `AT+SSID`                        |
| `setmac <mac>`| Set the destination MAC address for commands. Replace `<mac>` with the MAC address.             | `setmac AA:BB:CC:DD:EE:FF`       |
| `loadconfig <file>` | Load commands from a configuration file and execute them on the destination device.       | `loadconfig config.txt`          |

---

## Examples

### Scan for Devices
```bash
python libnetat.py eth0 --command scan
```

### Send a Command to a Specific MAC Address
```bash
python libnetat.py eth0 --command "AT+SSID" --dest_mac AA:BB:CC:DD:EE:FF
```

### Perform NETLOG Discovery(not working)
```bash
python libnetat.py eth0 --command netlog
```

### Run in Interactive Mode
```bash
python libnetat.py eth0
```

#### Interactive Commands Example:
```plaintext
>: scan
Found devices:
1. AA:BB:CC:DD:EE:FF
2. 11:22:33:44:55:66

>: setmac AA:BB:CC:DD:EE:FF
Destination MAC address set to AA:BB:CC:DD:EE:FF

>: AT+SSID
+SSID:tacosinsideofme
OK

>: exit
```

---

## Configuration File Format

Configuration files should contain commands in the format `CMD=VALUE` (e.g., for AT commands).

**Example `config.txt`:**
```plaintext
ssid=tacos
mcs=255
```

Run with:
```bash
python libnetat.py eth0 --config_file config.txt
```

---

## Logging

The script logs activity, errors, and debug information. By default, logs are saved to `netat_mgr.log`. Use the `--logfile` option to specify a different file.

**Log File Example:**
```plaintext
2024-12-03 10:00:00 - INFO - Starting NetatMgr
2024-12-03 10:00:01 - DEBUG - Sent data to ('<broadcast>', 56789): b'...'
2024-12-03 10:00:02 - INFO - Discovered device: AA:BB:CC:DD:EE:FF
```

---

## Notes

- Ensure the specified network interface (`<interface>`) is active and properly configured.
- Commands requiring a MAC address (`--dest_mac`) will fail if the MAC is not valid or reachable.
- For help or troubleshooting, check the log file specified with `--logfile`.


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
