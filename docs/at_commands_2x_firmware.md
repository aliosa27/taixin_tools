# 2.x Firmware AT Commands Reference

This document provides a reference for the AT commands supported by the 2.x firmware for NetAT mode.

## Basic Networking Commands

### AT+WIFIMODE - Set the working mode

**Query:**
```
AT+WIFIMODE=?
```

**Setting:**
```
AT+WIFIMODE=ap
```

**Response:**
```
OK
```

**Parameters:**
- Supports 5 modes:
  - `ap`: Standard protocol AP mode
  - `sta`: STA mode of standard protocol
  - `apsta`: Standard protocol relay mode. In relay mode, the device acts as a STA to connect to the previous level AP and also acts as an AP to provide connection services to other STAs.
  - `wnbap`: Private protocol AP mode, can be interconnected with STA V1.6 (not supported by default firmware)
  - `wnbsta`: STA mode of private protocol, can be interconnected with V1.6 AP (not supported by default firmware)

### AT+SSID - Set the SSID

**Query:**
```
AT+SSID=?
```

**Setting:**
```
AT+SSID=ssid_char
```

**Response:**
```
+ SSID:HALOW_959B60
OK
```

**Parameters:**
- The default SSID is HALOW_xxxxxx (the last 3 bytes of MAC)
- ssid_char length is less than or equal to 32 characters, exceeding will be truncated.

**Example:**
```
at+ssid=hgic_ah_test
```

### AT+ENCRYPT - Set encryption mode

**Query:**
```
AT+ENCRYPT=?
```

**Setting:**
```
AT+ENCRYPT=0/1
```

**Response:**
```
+ ENCRYPT:0 or 1
OK
```

**Parameters:**
- `1`: Enable encryption
- `0`: Disable encryption

**Example:**
```
at+encrypt=1
at+encrypt=0
```

### AT+KEY - Set encryption password

**Query:**
```
AT+KEY=?
```

**Setting:**
```
AT+KEY=key_char
```

**Response:**
```
+ KEY:key_char
OK
```

**Parameters:**
- The default key is 12345678
- The length of key_char must be greater than or equal to 8 characters (ASCII characters).
- When the key length is less than 8, it returns: ERROR need 8 bytes at less

**Example:**
```
at+key=87654321
```

### AT+PAIR - Pairing control

**Setting:**
```
AT+PAIR=0/1/2/...
```

**Response:**
```
OK
```

**Parameters:**
- This command can realize fast pairing and networking.
- Before starting pairing, the AP is configured with SSID and key. By pairing, the STA will obtain the AP's SSID and key.
- After pairing is successful, a PAIRING SUCCESS message will be generated, but the pairing will not be automatically terminated.
- Execute AT+PAIR=0 to stop pairing.
- The connection will be automatically established after pairing stops.
- If both AP and STA have set SSID and other parameters, there is no need to start PAIR. Parameters are automatically connected.

**Example:**
```
AT+PAIR=1 // Start pairing, pair according to the default group
AT+PAIR=0 // Stop pairing
AT+PAIR=2 // Start pairing and pair according to group 2
```

### AT+CHAN_LIST - Set channel list

**Query:**
```
AT+CHAN_LIST=?
```

**Setting:**
```
AT+CHAN_LIST=freq1,freq2
```

**Response:**
```
+ CHAN_LIST:9080,9160,9240
OK
```

**Parameters:**
- This command is used to set the frequency list
- The specified frequency value is the center frequency*10, for example 9080 express 908MHz
- Supports up to 16 frequency points, separated by commas

**Example:**
```
AT+CHAN_LIST=9080,9240
```

### AT+BSS_BW - Set BSS bandwidth

**Query:**
```
AT+BSS_BW=?
```

**Setting:**
```
AT+BSS_BW=bss_bw
```

**Response:**
```
+ BSS_BW:8MHz
OK
```

**Parameters:**
- bss_bw selects only the following 4 values:
  - `1`: 1MHz
  - `2`: 2MHz
  - `4`: 4MHz
  - `8`: 8MHz

**Example:**
```
at+bss_bw=4
```

## Advanced Networking Commands

### AT+TXPOWER - Set the maximum transmit power

**Query:**
```
AT+TXPOWER=?
```

**Setting:**
```
AT+TXPOWER=txpower
```

**Response:**
```
+ TXPOWER:20dbm
OK
```

**Parameters:**
- This command is used to manually set the maximum transmit power.
- The range is 1~20, 1db step.
- Any settings outside the range will be set to 20.

**Example:**
```
at+txpower=20
```

### AT+ACKTMO - Set ACK TIMEOUT time

**Query:**
```
AT+ACK_TO=?
```

**Setting:**
```
AT+ACK_TO=xx
```

**Response:**
```
+ ACK_TO:extra ack timeout=0us
OK
```

**Parameters:**
- Set and add AH module WiFi protocol parameter ack timeout value in microseconds, default is 0.
- This setting is only required when communicating over 1km.
- This parameter is calculated as 10*(distance in kilometers - 1), for example, 2km, set ack_to=10.
- Modified values are not saved when power is off.

**Example:**
```
AT+ACK_TO=100
```

### AT+UNPAIR - Set to unassign STA Pairing

**Query:**
```
AT+UNPAIR=?
```

**Setting:**
```
AT+UNPAIR=mac_addr
```

**Response:**
```
No response
```

**Parameters:**
- mac_addr is the MAC address of the other party

**Example:**
```
at+unpair=f6:de:09:75:a3:61
```

### AT+APHIDE - Hide AP Information

**Query:**
```
AT+APHIDE=?
```

**Setting:**
```
AT+APHIDE=0/1
```

**Response:**
```
+ APHIDE:1
OK
```

**Parameters:**
- Execute this command in AP mode to control whether the AP SSID can be scanned
- `0`: Can be scanned
- `1`: Unable to scan

**Example:**
```
at+aphide=1
```

### AT+SCAN - Scan surrounding AP information

**Execute:**
```
AT+SCAN
```

**Response:**
```
OK
```

**Description:**
- Exist STA Mode executes this command to scan the surrounding AP information.
- Can be umac of dbg Scanned data is printed AP information: at+sysdbg=umac,1

### AT+CHANNEL - Set channel

**Query:**
```
AT+CHANNEL=?
```

**Setting:**
```
AT+CHANNEL=channel-index
```

**Response:**
```
+ CHANNEL:3
OK
```

**Parameters:**
- The minimum value of Channel is 1 and less than or equal to the number of values in chanlist
- Usually set on the AP side

**Example:**
```
AT+CHANNEL=1
```

## Debug Commands

### AT+SYSCFG - View device parameter information

**Execute:**
```
AT+SYSCFG
```

**Description:**
- View device parameter information

### AT+FWUPG - Serial port firmware upgrade

**Execute:**
```
AT+FWUPG
```

**Response:**
- After successful execution, the serial port prints: CCCCCCCCCC
- Indicates that the module has entered the upgrade mode and can use the xmodem protocol to download the firmware.

**Description:**
- Serial port tools that support the xmodem protocol include: secureCRT, xshell

### AT+LOADDEF - Restore factory settings

**Execute:**
```
AT+LOADDEF=1
```

**Description:**
- Restore factory settings

### AT+SYSDBG - Set to print debug information

**Setting:**
```
AT+SYSDBG=XXX,VALE
```

**Response:**
```
OK
```

**Parameters:**
- XXX can select:
  - `LMAC`: Air interface statistics
  - `UMAC`: Upper layer protocol stack information
- VALE=0 means turn off the corresponding printing, =1 means turn on

**Example:**
```
AT+SYSDBG=LMAC,1
```

### AT+RST - Device restart

**Execute:**
```
AT+RST
```

**Description:**
- Reset the device

### AT+JTAG - Enable or disable debug port

**Setting:**
```
AT+JTAG=0/1
```

**Response:**
```
OK
```

**Parameters:**
- Need to be used with a debugger
- `0`: Off
- `1`: Open

**Example:**
```
AT+JTAG=1
```

### AT+TX_PWR_SUPER - Set SUPER PWR

**Query:**
```
AT+TX_PWR_SUPER=?
```

**Setting:**
```
AT+TX_PWR_SUPER=1/0
```

**Response:**
```
tx pwr super enable or tx pwr super disable
```

**Parameters:**
- This command is used to manually set whether to enable Superpwr
- In normal mode, it is enabled by default
- In test mode, it is closed by default

**Example:**
```
AT+TX_PWR_SUPER=1
```

### AT+VERSION - Check the firmware version

**Query:**
```
AT+VERSION
```

**Response:**
```
+ VERSION:v2.4.1.3-34690, app:0
```

**Parameters:**
- Supported after build 34690
- v2.4.1.3-34690, app:0, where:
  - v2 is the main version
  - 4 is the branch version
  - 1 is the patch version
  - 3 is the bridge type firmware (if this bit is 5, it indicates fmac firmware)

## Hibernation Related Commands

### AT+DSLEEP - Set to sleep

**Query:**
```
AT+DSLEEP=?
```

**Setting:**
```
AT+DSLEEP=1
```

**Response:**
```
+DSLEEP:0
OK
```

**Parameters:**
- Cannot read after hibernation
- In the connected state, set = 1 to make the device enter the rest state, sleep and keep alive state
- In the non-connected state, setting = 1 means the device enters the rest state, sleep for 60 seconds and then wake up

**Example:**
```
AT+DSLEEP=1
```

### AT+WAKEUP - Set up remote wake-up

**Query:**
```
AT+WAKEUP=?
```

**Setting:**
```
AT+WAKEUP=mac_addr
```

**Response:**
```
invalid
```

**Parameters:**
- Enter this command on the AP to wake up the sleeping STA

**Example:**
```
AT+WAKEUP=11:22:33:44:55:66
```

## Relay Related Setting Commands

### AT+R_SSID - Set up the relay to connect to the next level SSID

**Query:**
```
AT+R_SSID=?
```

**Setting:**
```
AT+R_SSID=repeater_ssid
```

**Response:**
```
+ R_SSID:repeater_ssid
OK
```

**Parameters:**
- Setting up a relay connection Down SSID of the primary STA.

**Example:**
```
AT+R_SSID=relay_ssid_example
```

### AT+R_KEY - Set the encryption password for the relay and the next level connection

**Query:**
```
AT+R_KEY=?
```

**Setting:**
```
AT+R_KEY=key_char
```

**Response:**
```
+ R_KEY:key_char
OK
```

**Parameters:**
- Setting up a relay connection Down The KEY of the first-level STA.
- The length of key_char must be greater than or equal to 8 hexadecimal characters.
- When the key length is less than 8, it returns: ERROR need 8 bytes at less

**Example:**
```
AT+R_KEY=87654321
```

## Roaming Related Setting Commands

### AT+ROAM - Set roaming enable

**Query:**
```
AT+ROAM=?
```

**Setting:**
```
AT+ROAM=0/1
```

**Response:**
```
OK
```

**Parameters:**
- Roaming needs to be enabled only on the STA side.
- The SSID of the AP in the roaming network can be set by full word matching or fuzzy matching:
  - Full word match: All APs' SSIDs are set to the same SSID. The length of the SSID is unlimited and should not exceed 32 characters. STAs are also set to this SSID.
  - Fuzzy matching: The last three characters of the SSID of different APs are different. The total length of the SSID must be greater than 8 characters, consisting of a common string (at the beginning of the SSID) and a 3-character ID (at the end of the string).
- Modified value is saved after power off.

**Example:**
```
AT+ROAM=1
```

## Network Related Commands

### AT+IPERF2 - TCP flow test

**Execute:**
```
AT+IPERF2=c/s,ip_addr,port,time
```

**Parameters:**
- `c/s`: "c" is for the client to send, "s" is for the server to receive
- `ip_addr`: the other party's IP address
- `port`: port number
- `time`: duration, unit S
- This command needs to enable the SYS_NETWORK_SUPPORT macro definition to be supported

**Example:**
```
Sending end: AT+IPERF2=c,192.168.123.2,5002,60
Receiving end: AT+IPERF2=s,5002
```

### AT+PING - Ping Function

**Execute:**
```
AT+PING=ip_domain,send_times,size
```

**Parameters:**
- `ip_domain` can be an IP address or a domain name
- Note that you cannot enter other at commands while pinging.
- This command requires the SYS_NETWORK_SUPPORT and LWIP_RAW macro definitions to be enabled.

**Example:**
```
AT+PING=192.168.123.2,5,1024
```

## Test Mode Related Commands

### AT+TEST_START - Set to enter or exit test mode

**Query:**
```
AT+TEST_START=?
```

**Setting:**
```
AT+TEST_START=1 or 0
```

**Response:**
```
1:+TEST_START:test mode started
0:+TEST_START: test mode stopped
OK
```

**Parameters:**
- Entering the test mode, you can perform RF Tx or Rx test
- This command will not be saved when power is off

**Example:**
```
AT+TEST_START=1
```

### AT+LO_FREQ - Set the frequency in test mode

**Query:**
```
AT+LO_FREQ=?
```

**Setting:**
```
AT+LO_FREQ=freq
```

**Response:**
```
LO freq = 924000 KHz
```

**Parameters:**
- Freq unit is KHz, for example, Freq=908000 means 908MHz
- This command is not saved when power is off

**Example:**
```
at+lo_freq=924000
```

### AT+TX_START - Set to enter or exit Tx model

**Query:**
```
AT+TX_START=?
```

**Setting:**
```
AT+TX_START=1 or 0
```

**Response:**
```
1:+TX_START:tx test started
0:+TX_START:tx test stopped
OK
```

**Parameters:**
- After entering test mode, select Enter Tx model, still Rx mode (default)
- This command is not saved when power is off

**Example:**
```
AT+TX_START=1
```

### AT+TX_MCS - Set up tx mcs

**Query:**
```
AT+TX_MCS=?
```

**Setting:**
```
AT+TX_MCS=xx
```

**Response:**
```
+ TX_MCS:255
OK
```

**Parameters:**
- 255 means automatic adjustment of mcs
- Set up tx mcs, the range is 0~7 or 1M Mode 10
- When it is fixed to a certain mcs, other values indicate mcs automatic adjustment
- This command is not saved when power is off

**Example:**
```
AT+TX_MCS=2
```

## Command Usage Examples

### Basic instructions for module connection establishment

When the module is initialized, set the frequency, bandwidth, SSID, and password:

```
AT+CHAN_LIST=9080,9160,9240   # Set 3 Channels
AT+BSS_BW=8                   # Set 8M bandwidth
AT+SSID=hgic_ah_test          # Set SSID
AT+ENCRYPT=1                  # Enable encryption
AT+KEY=12345678               # Set encryption key
AT+WIFIMODE=ap                # Set to AP mode or STA mode
```

### Configuring relay network instructions

#### AP Modules
1. Configure AP's SSID:
```
at+ssid=ssid1
```

2. Configure not to encrypt (to simplify the configuration):
```
at+encrypt=0
```

#### Relay module
1. Configure the role of the relay:
```
at+mode=apsta
```

2. Configure not to encrypt:
```
at+encrypt=0
```

3. Configure the relay r_ssid, used to allow the relay to follow STA connection:
```
at+r_ssid=ssid1_r1
```

4. Configure the relay SSID, used to allow the relay to follow AP connection:
```
at+ssid=ssid1
```

#### STA Modules
1. Configure STA's SSID (should be the same as the relay's r_ssid):
```
at+ssid=ssid1_r1
```

2. Configure not to encrypt:
```
at+encrypt=0
```