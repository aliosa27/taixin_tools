# NetAT Protocol Documentation

## Overview

The NetAT protocol is a UDP-based communication protocol designed for configuring and managing Taixin wireless devices. It provides a mechanism for sending AT commands over a network connection, retrieving device information, and managing device configurations.

## Protocol Basics

### Transport Layer

NetAT runs over UDP, typically using port 56789. This choice allows for:
- Lightweight communications without the overhead of TCP
- Broadcast capabilities for device discovery
- Low latency command-response cycles

### Packet Structure

The basic structure of a NetAT packet is as follows:

```
+---------------+---------------+---------------+---------------+
|     CMD       |     LEN       |     DEST      |     SRC       |
| (1 byte)      | (2 bytes)     | (6 bytes)     | (6 bytes)     |
+---------------+---------------+---------------+---------------+
|                         PAYLOAD                               |
| (variable length)                                             |
+---------------+---------------+---------------+---------------+
```

- **CMD**: Command type identifier
- **LEN**: Length of the packet payload
- **DEST**: Destination MAC address (6 bytes)
- **SRC**: Source identifier/cookie (6 bytes)
- **PAYLOAD**: Variable length data specific to the command type

### Command Types

The NetAT protocol defines several command types:

1. **WNB_NETAT_CMD_SCAN_REQ (1)**: Request to scan for devices
2. **WNB_NETAT_CMD_SCAN_RESP (2)**: Response to a scan request
3. **WNB_NETAT_CMD_AT_REQ (3)**: AT command request
4. **WNB_NETAT_CMD_AT_RESP (4)**: AT command response

## Protocol Operation

### Device Discovery

Device discovery is performed using a broadcast scan request:

1. The client sends a `WNB_NETAT_CMD_SCAN_REQ` packet with:
   - DEST: Broadcast MAC address (FF:FF:FF:FF:FF:FF)
   - SRC: A unique client identifier/cookie
   - PAYLOAD: Empty or containing scan parameters

2. Available devices respond with `WNB_NETAT_CMD_SCAN_RESP` packets containing:
   - DEST: The client's SRC value from the request
   - SRC: The device's MAC address
   - PAYLOAD: Device information (name, capabilities, etc.)

### AT Command Communication

Once a device is discovered, the client can send AT commands:

1. The client sends a `WNB_NETAT_CMD_AT_REQ` packet with:
   - DEST: The target device's MAC address
   - SRC: The client's identifier/cookie
   - PAYLOAD: The AT command string (e.g., "AT+MODE?")

2. The device responds with a `WNB_NETAT_CMD_AT_RESP` packet containing:
   - DEST: The client's SRC value
   - SRC: The device's MAC address
   - PAYLOAD: The AT command response

## Implementation Guidelines

### Packet Creation

To create a NetAT packet:

1. Create a 1-byte command type field (CMD)
2. Calculate the payload length and create a 2-byte length field (LEN)
3. Set the 6-byte destination MAC address (DEST)
4. Set the 6-byte source identifier/cookie (SRC)
5. Append the variable-length payload data
6. Concatenate all fields in the correct order

### Packet Parsing

To parse a received NetAT packet:

1. Verify the packet is at least 15 bytes (minimum size with no payload)
2. Extract the first byte as the command type (CMD)
3. Extract the next 2 bytes as the payload length (LEN)
4. Extract the next 6 bytes as the destination MAC address (DEST)
5. Extract the next 6 bytes as the source identifier (SRC)
6. Extract the remaining bytes as the payload

### Sending Packets

NetAT packets are typically sent using raw sockets:

1. For broadcast packets:
   - Set destination MAC to broadcast (FF:FF:FF:FF:FF:FF)
   - Set destination IP to broadcast (255.255.255.255)
   - Use UDP with source and destination port 56789

2. For unicast packets:
   - Set destination MAC to the target device's MAC address
   - Set destination IP to the target device's IP address
   - Use UDP with source and destination port 56789

## AT Command Formats

NetAT supports several types of AT commands:

### Query Commands
Format: `AT+<COMMAND>?`
Example: `AT+MODE?`
Purpose: Retrieve current settings or status

### Set Commands
Format: `AT+<COMMAND>=<VALUE>`
Example: `AT+MODE=ap`
Purpose: Configure device settings

### Execute Commands
Format: `AT+<COMMAND>`
Example: `AT+RESET`
Purpose: Execute actions without parameters

## Packet Capture and Processing

The NetAT protocol implementation typically involves:

1. Packet Capture Setup:
   - Set up a network packet capture on UDP port 56789
   - Filter for packets matching the NetAT protocol structure
   - Implement a mechanism to stop capture when needed
   - Store captured packets for processing

2. Packet Processing:
   - Examine each captured UDP packet
   - Extract the raw data payload
   - Parse the data according to the NetAT packet structure
   - Process packets based on command type:
     * Handle scan responses (type 2)
     * Handle AT command responses (type 4)
   - Remove processed packets from the queue

## Security Considerations

The NetAT protocol has several security considerations:

1. **No Encryption**: Communications are not encrypted, so sensitive commands and responses can be intercepted.

2. **No Authentication**: There is no built-in authentication mechanism to verify the identity of clients or devices.

3. **Broadcast Vulnerability**: The protocol relies on broadcast for discovery, which can be exploited for reconnaissance.

4. **Command Injection**: Without proper validation, malformed AT commands could potentially be used for injection attacks.

## Common Usage Patterns

### Device Discovery and Selection

1. Send a broadcast scan request packet
2. Wait for a defined timeout period to collect responses
3. Process discovered devices from the responses
4. Select a device for communication based on the discovery results

### Sending AT Commands

1. Create an AT command request packet (e.g., "AT+MODE?")
2. Send the packet to the selected device
3. Wait for the command response
4. Process the response data

### Configuration Management

1. Query multiple configuration parameters from a device
2. Store the configuration values
3. Modify configuration parameters as needed
4. Send configuration updates to the device


### Debugging Tools

1. **Packet Capture**: Use Wireshark or tcpdump to capture and analyze NetAT packets:
   ```bash
   sudo tcpdump -i eth0 udp port 56789 -vvv -X
   ```

## Advanced Topics

## Protocol Limitations

1. **Scalability**: The broadcast-based discovery doesn't scale well to large networks
2. **Reliability**: UDP doesn't guarantee delivery, so commands may be lost
3. **Bandwidth**: Large responses may be fragmented or lost
4. **Security**: Limited security features as noted above

## Future Enhancements

Potential improvements to the NetAT protocol include:

1. **Secure Transport**: Implementing TLS or DTLS for encrypted communications
2. **Authentication**: Adding authentication mechanisms for devices and clients
3. **Compression**: Adding payload compression for large configurations
4. **Reliable Delivery**: Implementing acknowledgments and retries for critical commands
5. **Service Discovery**: Using standardized service discovery protocols