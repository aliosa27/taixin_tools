#!/usr/bin/env python3

from scapy.all import *
import time
import threading
import os
import sys
from datetime import datetime


NETLOG_PORT = 64320
DISCOVERY_TIMEOUT = 5.0
HEARTBEAT_INTERVAL = 0.5

# Packet types
PKT_TYPE_DISCOVERY = 1
PKT_TYPE_DISCOVERY_RESP = 2  
PKT_TYPE_HEARTBEAT = 3
PKT_TYPE_LOG_DATA = 4

class NetlogPacket:
    def __init__(self, pkt_type=0, signature=b"\x00" * 6, data=b""):
        self.pkt_type = pkt_type
        self.signature = signature[:6].ljust(6, b'\x00')  # Ensure 6 bytes
        self.data = data
    
    def to_bytes(self):
        return bytes([self.pkt_type]) + self.signature + self.data
    
    @classmethod
    def from_bytes(cls, data):
        if len(data) < 7:
            raise ValueError("Packet too short")
        
        pkt_type = data[0]
        signature = data[1:7]
        payload = data[7:] if len(data) > 7 else b""
        
        return cls(pkt_type, signature, payload)

class NetlogClient:
    def __init__(self, interface=None, bind_ip=None, debug=False):
        self.interface = interface
        self.debug = debug
        
        if bind_ip:
            self.bind_ip = bind_ip
        elif interface:
            self.bind_ip = get_if_addr(interface)
            if not debug:
                print(f"Using interface: {interface} ({self.bind_ip})")
        else:
            self.bind_ip = "0.0.0.0"
            
        self.our_signature = os.urandom(6)  
        self.device_signature = None
        self.device_discovered = False
        self.discovered_devices = []  
        self.running = False
        self.heartbeat_thread = None
        self.log_file = None
        
        if debug:
            print(f"Using interface: {interface}")
            print(f"Bind IP: {self.bind_ip}")
            print(f"Our signature: {self.our_signature.hex()}")
        
    def setup_logging(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.device_signature:
            device_id = self.device_signature.hex()
            self.log_file = open(f"netlog_{device_id}_{timestamp}.txt", "w")
        else:
            self.log_file = open(f"netlog_{timestamp}.txt", "w")
            
    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}]: {message}"
        print(log_line)
        
        if self.log_file:
            self.log_file.write(log_line + "\n")
            self.log_file.flush()

    def send_discovery(self):
        if self.debug:
            print("Sending discovery packet...")
        
        packet = NetlogPacket(
            pkt_type=PKT_TYPE_DISCOVERY,
            signature=b"\xff" * 6,  # Broadcast signature
            data=self.our_signature
        )
        
        # Create raw packet
        raw_packet = packet.to_bytes()
        
        try:
            if self.interface:
                sock = conf.L2socket(iface=self.interface)
                eth_packet = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
                sock.send(eth_packet)
                sock.close()
            else:
                udp_packet = IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
                send(udp_packet, verbose=0)
        except Exception as e:
            if self.debug:
                print(f"Error sending discovery: {e}")
            # Fallback method
            udp_packet = IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
            send(udp_packet, verbose=0)

    def send_heartbeat(self):
        if not self.device_discovered or not self.device_signature:
            return
            
        packet = NetlogPacket(
            pkt_type=PKT_TYPE_HEARTBEAT,
            signature=self.device_signature,
            data=self.our_signature
        )
        
        raw_packet = packet.to_bytes()
        
        try:
            if self.interface:
                sock = conf.L2socket(iface=self.interface)
                eth_packet = Ether(dst="ff:ff:ff:ff:ff:ff") / IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
                sock.send(eth_packet)
                sock.close()
            else:
                udp_packet = IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
                send(udp_packet, verbose=0)
        except Exception as e:
            if self.debug:
                print(f"Error sending heartbeat: {e}")
            udp_packet = IP(src=self.bind_ip, dst="255.255.255.255") / UDP(sport=NETLOG_PORT, dport=NETLOG_PORT) / Raw(raw_packet)
            send(udp_packet, verbose=0)

    def heartbeat_worker(self):
        while self.running:
            if self.device_discovered:
                self.send_heartbeat()
            else:
                self.send_discovery()
            time.sleep(HEARTBEAT_INTERVAL)

    def packet_handler(self, packet):
        if not packet.haslayer(UDP) or packet[UDP].dport != NETLOG_PORT:
            return
            
        if not packet.haslayer(Raw):
            return
            
        if packet[IP].src == self.bind_ip:
            return
            
        try:
            raw_data = bytes(packet[Raw])
            if len(raw_data) < 7:  # Minimum packet size i think
                return
                

            netlog_pkt = NetlogPacket.from_bytes(raw_data)
            
            if self.debug:
                print(f"\nReceived packet:")
                print(f"  Type: {netlog_pkt.pkt_type}")
                print(f"  From: {packet[IP].src}:{packet[UDP].sport}")
                print(f"  Signature: {netlog_pkt.signature.hex()}")
                print(f"  Data length: {len(netlog_pkt.data)}")
                if netlog_pkt.data:
                    print(f"  Data: {netlog_pkt.data.hex()}")
            
            if netlog_pkt.pkt_type == PKT_TYPE_DISCOVERY_RESP:
                self.handle_discovery_response(netlog_pkt, packet[IP].src)
            elif netlog_pkt.pkt_type == PKT_TYPE_LOG_DATA:
                self.handle_log_data(netlog_pkt)
            elif netlog_pkt.pkt_type == PKT_TYPE_DISCOVERY:
                if self.debug:
                    print(f"  -> Discovery packet from another client")
            elif netlog_pkt.pkt_type == PKT_TYPE_HEARTBEAT:
                if self.debug:
                    print(f"  -> Heartbeat packet")
            else:
                if self.debug:
                    print(f"  -> Unknown packet type: {netlog_pkt.pkt_type}")
                
        except Exception as e:
            if self.debug:
                print(f"Error parsing packet: {e}")
                if packet.haslayer(Raw):
                    raw_data = bytes(packet[Raw])
                    print(f"Raw packet data ({len(raw_data)} bytes): {raw_data.hex()}")
                    if len(raw_data) > 0:
                        print(f"First byte (type): {raw_data[0]}")
                        if len(raw_data) >= 7:
                            print(f"Signature bytes: {raw_data[1:7].hex()}")
            return

    def handle_discovery_response(self, netlog_pkt, src_ip):
        if self.debug:
            print(f"\n*** DISCOVERY RESPONSE from {src_ip} ***")
        
        if len(netlog_pkt.data) >= 6:
            device_signature = netlog_pkt.data[:6]
        else:
            device_signature = netlog_pkt.signature
            
        device_info = {
            'signature': device_signature,
            'ip': src_ip,
            'id': device_signature.hex()
        }
        
        for existing in self.discovered_devices:
            if existing['signature'] == device_signature:
                return  
        
        self.discovered_devices.append(device_info)
        
        if not self.debug:
            print(f"Discovered device: {device_info['id']} at {src_ip}")
        else:
            print(f"Added device to discovery list: {device_info['id']} at {src_ip}")

    def select_device(self):
        if len(self.discovered_devices) == 0:
            return False
        elif len(self.discovered_devices) == 1:
            device = self.discovered_devices[0]
            self.device_signature = device['signature']
            self.device_discovered = True
            print(f"Selected device: {device['id']} at {device['ip']}")
            return True
        else:
            print(f"\nFound {len(self.discovered_devices)} devices:")
            for i, device in enumerate(self.discovered_devices):
                print(f"  {i+1}. {device['id']} at {device['ip']}")
            
            while True:
                try:
                    choice = input(f"Select device (1-{len(self.discovered_devices)}): ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.discovered_devices):
                        device = self.discovered_devices[idx]
                        self.device_signature = device['signature']
                        self.device_discovered = True
                        print(f"Selected device: {device['id']} at {device['ip']}")
                        return True
                    else:
                        print("Invalid selection. Try again.")
                except (ValueError, KeyboardInterrupt):
                    print("Invalid input. Try again.")
                    continue

    def handle_log_data(self, netlog_pkt):
        if self.debug:
            print(f"\n*** NETLOG DATA RECEIVED ***")
        
        if not self.device_discovered:
            if self.debug:
                print("No device selected yet, ignoring log data")
            return
            
        # Check if this log data is from our selected device
        # The signature field should match our signature (indicating it's for us)
        if netlog_pkt.signature != self.our_signature:
            if self.debug:
                print(f"Log data not for us (signature: {netlog_pkt.signature.hex()})")
            return
            
        try:
            log_data = netlog_pkt.data
            if len(log_data) > 6:  # Skip the device MAC (first 6 bytes)
                log_text = log_data[6:].decode('utf-8', errors='ignore').strip()
                if log_text:
                    print(log_text)
                    if self.debug:
                        self.log_message(log_text)
            else:
                if self.debug:
                    print(f"Log data too short: {len(log_data)} bytes")
                    print(f"Raw data: {log_data.hex()}")
        except Exception as e:
            if self.debug:
                print(f"Error processing log data: {e}")
                print(f"Raw data: {netlog_pkt.data.hex()}")

    def discover_devices(self):
        if not self.debug:
            print("Scanning for NETLOG devices...")
        else:
            print("Starting device discovery...")
        
        # Start packet capture
        filter_str = f"udp port {NETLOG_PORT}"
        
        # Start heartbeat thread
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_worker)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        self.send_discovery()
        
        discovery_timeout = 3.0  # 3 seconds to discover devices
        start_time = time.time()
        
        if self.debug:
            print(f"Listening for devices on port {NETLOG_PORT}...")
            print("Press Ctrl+C to stop")
        
        try:
            while time.time() - start_time < discovery_timeout:
                if self.interface:
                    packets = sniff(iface=self.interface, filter=filter_str, timeout=0.5, store=True)
                else:
                    packets = sniff(filter=filter_str, timeout=0.5, store=True)
                
                for packet in packets:
                    self.packet_handler(packet)
            
            if self.select_device():
                if self.debug:
                    self.setup_logging()
                
                if self.debug:
                    print("Sending initial heartbeat...")
                else:
                    print("Starting log reception...")
                    
                self.send_heartbeat()
                
                if self.interface:
                    sniff(iface=self.interface, filter=filter_str, prn=self.packet_handler, store=0)
                else:
                    sniff(filter=filter_str, prn=self.packet_handler, store=0)
            else:
                print("No devices found or selected.")
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.running = False
            if self.log_file:
                self.log_file.close()

def list_interfaces():
    print("Available interfaces:")
    for iface in get_if_list():
        ip = get_if_addr(iface)
        print(f"  {iface}: {ip}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 netlog.py <interface> [--debug]")
        print("\nAvailable interfaces:")
        list_interfaces()
        print("\nOptions:")
        print("  --debug       Enable verbose debugging output")
        sys.exit(1)
    
    interface = sys.argv[1]
    bind_ip = None
    debug = False
    
    for arg in sys.argv[2:]:
        if arg == "--debug":
            debug = True
        elif not bind_ip and not arg.startswith("--"):
            bind_ip = arg
    
    if interface not in get_if_list():
        print(f"Interface '{interface}' not found.")
        list_interfaces()
        sys.exit(1)
    
    # Auto-detect IP if not provided
    if not bind_ip:
        bind_ip = get_if_addr(interface)
        if bind_ip == "0.0.0.0":
            print(f"Warning: Interface {interface} has no IP address assigned")
        elif debug:
            print(f"Auto-detected IP: {bind_ip}")
    
    client = NetlogClient(interface=interface, bind_ip=bind_ip, debug=debug)
    client.discover_devices()

if __name__ == "__main__":
    main()