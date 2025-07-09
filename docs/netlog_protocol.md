# NetLog Protocol Documentation

## Overview

The NetLog protocol is a UDP-based communication protocol designed for receiving log messages from Taixin wireless devices. It operates alongside the NetAT protocol but serves a different purpose - while NetAT is for device configuration and management, NetLog provides real-time logging functionality.

## Protocol Basics

### Transport Layer

NetLog runs over UDP, typically using port 64320. This choice provides:
- Low overhead for frequent log messages
- No connection establishment or teardown requirements
- Ability to maintain log streaming even during device configuration

### Packet Structure

The basic structure of a NetLog packet is as follows:

```
+---------------+---------------+---------------+
|     TYPE      |   SIGNATURE   |     DATA      |
| (1 byte)      | (6 bytes)     | (variable)    |
+---------------+---------------+---------------+
```

- **TYPE**: Packet type identifier (1 byte)
- **SIGNATURE**: Device or client signature (6 bytes)
- **DATA**: Variable length data specific to the packet type

### Packet Types

The NetLog protocol defines four packet types:

1. **DISCOVERY (1)**: Sent by clients to discover devices that support NetLog
2. **DISCOVERY_RESP (2)**: Sent by devices in response to discovery packets
3. **HEARTBEAT (3)**: Sent by clients to maintain an active log connection
4. **LOG_DATA (4)**: Sent by devices to deliver log messages to clients

## Protocol Operation

### Discovery Phase

The discovery phase identifies devices that support the NetLog protocol:

1. The client sends a DISCOVERY packet with:
   - TYPE: 1 (DISCOVERY)
   - SIGNATURE: Broadcast signature (all 0xFF)
   - DATA: Client's unique signature (6 bytes)

2. Devices respond with DISCOVERY_RESP packets containing:
   - TYPE: 2 (DISCOVERY_RESP)
   - SIGNATURE: Device signature (6 bytes)
   - DATA: Device information (optional)

### Connection Maintenance

Once a device is discovered, the client maintains the connection:

1. The client sends HEARTBEAT packets regularly with:
   - TYPE: 3 (HEARTBEAT)
   - SIGNATURE: Target device's signature
   - DATA: Client's signature (6 bytes)

2. If the device doesn't receive heartbeats for a certain period, it will stop sending log data to that client.

### Log Data Transmission

When a device has log data to send:

1. The device sends LOG_DATA packets containing:
   - TYPE: 4 (LOG_DATA)
   - SIGNATURE: Target client's signature
   - DATA: Device signature (6 bytes) + UTF-8 log text

## Implementation Guidelines

### Packet Creation

To create a NetLog packet:

1. Create a 1-byte packet type field (TYPE)
2. Set the 6-byte signature field (SIGNATURE)
3. Append the variable-length data field (DATA)
4. Concatenate all fields in the correct order

### Packet Parsing

To parse a received NetLog packet:

1. Verify the packet is at least 7 bytes (minimum packet size)
2. Extract the first byte as the packet type (TYPE)
3. Extract the next 6 bytes as the signature (SIGNATURE)
4. Extract the remaining bytes as the data (DATA)

### Discovery Process

To implement the device discovery process:

1. Create a DISCOVERY packet with:
   - TYPE: 1 (DISCOVERY)
   - SIGNATURE: Broadcast signature (all 0xFF)
   - DATA: Client's unique signature (6 bytes)

2. Send the packet using UDP broadcast:
   - Destination MAC: Broadcast (FF:FF:FF:FF:FF:FF)
   - Destination IP: Broadcast (255.255.255.255)
   - UDP port: 64320 (both source and destination)

3. Process incoming DISCOVERY_RESP packets:
   - Store device information for connection establishment
   - Record device signature and network address

### Heartbeat Mechanism

To maintain an active connection:

1. Periodically send HEARTBEAT packets to discovered devices:
   - TYPE: 3 (HEARTBEAT)
   - SIGNATURE: Target device's signature
   - DATA: Client's signature (6 bytes)

2. Recommended heartbeat interval: 500ms - 1000ms
   - Adjust based on network conditions and application requirements
   - Shorter intervals provide faster reconnection but higher network load

### Log Data Processing

When receiving LOG_DATA packets:

1. Verify the packet is intended for this client (check SIGNATURE)
2. Extract the log data from the DATA field:
   - First 6 bytes: Device signature
   - Remaining bytes: UTF-8 encoded log text
3. Process and display the log message
4. Optionally store logs for later analysis

## Working with Multiple Interfaces

In environments with multiple network interfaces:

1. Select the appropriate network interface for NetLog communications
2. Configure packet capture and transmission to use the selected interface
3. Consider fallback mechanisms if the primary interface fails
4. For multi-homed systems, consider running separate NetLog clients on each interface

## Security Considerations

The NetLog protocol has several security considerations:

1. **No Encryption**: Log messages are not encrypted, so sensitive information can be intercepted.

2. **No Authentication**: There is no built-in authentication to verify clients or devices.

3. **Broadcast Discovery**: The protocol relies on broadcast for discovery, which can be exploited.

4. **Potential for Log Injection**: Without proper validation, malformed log messages could potentially be injected.


## Simultaneous NetAT and NetLog Operation

A key feature of the NetLog protocol is its ability to operate alongside NetAT. This allows for:

1. Concurrent device configuration and log monitoring
2. Real-time feedback during device configuration
3. Monitoring of command execution effects
4. Enhanced debugging capabilities

To implement dual-mode operation:

1. Initialize separate components for NetAT and NetLog functionality
2. Use separate packet captures or filters for each protocol
3. Maintain independent connection state for each protocol
4. Coordinate client identifiers between protocols if needed

## Advanced Topics

## Troubleshooting

### Debugging Tools

1. **Packet Capture**: Use Wireshark or tcpdump to capture and analyze NetLog packets:
   ```bash
   sudo tcpdump -i eth0 udp port 64320 -vvv -X
   ```

2. **Debug Mode**: Enable debug mode in your implementation to view detailed protocol operations

3. **Standalone Sniffer**: Use a standalone NetLog sniffer to verify packet structure

## Future Enhancements

Potential improvements to the NetLog protocol include:

1. **Secure Transport**: Implementing TLS or DTLS for encrypted log messages
2. **Authentication**: Adding authentication mechanisms for clients and devices
3. **Compression**: Adding log message compression for efficient bandwidth usage
4. **Reliable Delivery**: Implementing acknowledgments and retries for critical log messages
5. **Structured Logging**: Supporting structured log formats like JSON