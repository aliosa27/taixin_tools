#!/usr/bin/env python3

import logging
import socket
import struct
import random
import time
import sys
import argparse
import platform
import os
import threading
from datetime import datetime

try:
    from scapy.all import *
    from scapy.layers.inet import IP, UDP
    from scapy.layers.l2 import Ether
    from scapy.sendrecv import srp, send, sendp
    from scapy.arch import get_if_list, get_if_addr, get_if_hwaddr
    from scapy.config import conf
    HAS_SCAPY = True
    conf.verb = 0
    import warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    warnings.filterwarnings("ignore", message=".*iface.*has no effect.*")
except ImportError:
    HAS_SCAPY = False
    print("ERROR: Scapy not found. Please install it:")
    print("pip install scapy")
    sys.exit(1)

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

try:
    import curses
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False

NETAT_BUFF_SIZE = 4096
NETAT_PORT = 56789
NETLOG_PORT = 64320

WNB_NETAT_CMD_SCAN_REQ = 1
WNB_NETAT_CMD_SCAN_RESP = 2
WNB_NETAT_CMD_AT_REQ = 3
WNB_NETAT_CMD_AT_RESP = 4

IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

PRODUCTION_SET_COMMANDS = [
    'mode', 'ssid', 'keymgmt', 'psk', 'pair', 'bss_bw', 'freq_range', 'chan_list', 'txpower', 'acktmo', 'tx_mcs',
    'joingroup', 'r_ssid', 'r_psk', 'roam', 'loaddef', 'fwupg', 'beacon_int', 'dtim_period', 'agg_cnt', 'wakeup',
    'heart_int', 'country_region', 'channel', 'rts_threshold', 'frag_threshold', 'bssid_filter', 'tx_bw', 'acs',
    'bgrssi', 'paired_stas', 'pairing', 'radio_onoff', 'join_group', 'ether_type', 'ps_connect',
    'bss_max_idle', 'wkio_mode', 'disassoc_sta', 'ps_mode', 'aplost_time', 'unpair', 'auto_chswitch', 'mcast_key',
    'reassoc_wkhost', 'wakeup_io', 'dbginfo', 'sysdbg', 'primary_chan', 'autosleep_time', 'super_pwr', 'auto_save',
    'pair_autostop', 'dcdc13', 'pa_pwrctl_dis', 'dhcpc', 'wkdata_save', 'mcast_txparam', 'reset_sta', 'ant_auto',
    'ant_sel', 'wkhost_reason', 'macfilter', 'atcmd', 'roaming', 'ap_hide', 'max_txcnt', 'assert_holdup', 'ap_psmode',
    'dupfilter', 'dis_1v1m2u', 'dis_psconnect', 'reset', 'heartbeat', 'heartbeat_resp', 'wakeup_data', 'custmgmt',
    'mgmtframe', 'wkdata_mask', 'driverdata', 'freqinfo', 'blenc', 'sleep', 'hwscan', 'user_edca', 'fix_txrate',
    'nav_max', 'clr_nav', 'cca_param', 'tx_modgain', 'rts_duration', 'disable_print', 'conn_paironly', 'diffcust_conn',
    'wait_psmode', 'standby', 'ap_chansw', 'cca_ce', 'rtc', 'apep_padding', 'watchdog', 'retry_fallback_cnt',
    'fallback_mcs', 'xosc', 'freq_cali_period', 'cust_drvdata', 'max_txdelay', 'heartbeat_int'
]

PRODUCTION_GET_COMMANDS = [
    'mode', 'ssid', 'keymgmt', 'psk', 'bss_bw', 'freq_range', 'chan_list', 'txpower', 'acktmo', 'tx_mcs', 'rssi',
    'conn_state', 'wnbcfg', 'sta_list', 'scan_list', 'bssid', 'agg_cnt', 'battery_level', 'module_type', 'disassoc_reason',
    'ant_sel', 'wkreason', 'wkdata_buff', 'temperature', 'sta_count', 'txq_param', 'nav', 'rtc', 'bgrssi', 'center_freq',
    'acs_result', 'reason_code', 'status_code', 'dhcpc_result', 'xosc', 'freq_offset', 'fwinfo', 'stainfo', 'signal'
]

DEBUG_SET_COMMANDS = [
    'acs_start', 'ack_to', 'adc_dump', 'ap_sleep_mode', 'ant_auto', 'ant_ctrl', 'ant_def', 'ant_dual', 'bgrssi_margin',
    'bgrssi_max', 'bgrssi_spur', 'bus_wt', 'cca_ce', 'cca_obsv', 'ccmp_support', 'chan_scan', 'cs_cnt', 'cs_en',
    'cs_num', 'cs_period', 'cs_th', 'cts_dup', 'edca_aifs', 'edca_cw', 'edca_txop', 'evm_margin', 'freq_list',
    'ft_att', 'lmac_dbgsel', 'lo_freq', 'mac_addr', 'mcast_bw', 'mcast_dup', 'mcast_mcs', 'mcast_reorder', 'mcast_rts',
    'nor_rd', 'obss_cca_diff', 'obss_edca', 'obss_nav_diff', 'obss_per', 'obss_switch', 'obss_th', 'pcf_en',
    'pcf_percent', 'pcf_period', 'phy_reset', 'print_period', 'pri_chan', 'qa_att', 'qa_cfg', 'qa_results', 'qa_rxthd',
    'qa_start', 'qa_txthd', 'radio_onoff', 'rc_new', 'reg_rd', 'reg_wt', 'rf_reset', 'rts_dup', 'rx_reorder',
    'set_agc', 'set_agc_th', 'set_bgrssi', 'set_bgrssi_avg', 'set_rts', 'set_vdd13', 'short_gi', 'short_th',
    'sleep_en', 'sta_psk', 'test_start', 'tx_agg_auto', 'tx_attn', 'tx_bw', 'tx_bw_dynamic', 'tx_cont', 'tx_cnt_max',
    'tx_cw', 'tx_delay', 'tx_dst_addr', 'tx_fc', 'tx_flags', 'tx_len', 'tx_max_agg', 'tx_max_syms', 'tx_mcs_max',
    'tx_mcs_min', 'txop_en', 'tx_ordered', 'tx_pha_amp', 'tx_pwr_auto', 'tx_pwr_max', 'tx_pwr_super', 'tx_pwr_super_th',
    'tx_rate_fixed', 'tx_start', 'tx_step', 'tx_trig', 'tx_trv_pilot_en', 'tx_type', 'wake_en', 'xo_cs', 'xo_cs_auto'
]

DEBUG_GET_COMMANDS = [
    'efuse_mac', 'lo_table', 'ps_check', 'rx_agc', 'rx_err', 'rx_evm', 'rx_pkts', 'rx_rssi', 'sta_info', 't_sensor',
    'tx_fail', 'tx_pkts'
]

SET_COMMANDS = PRODUCTION_SET_COMMANDS + DEBUG_SET_COMMANDS
GET_COMMANDS = PRODUCTION_GET_COMMANDS + DEBUG_GET_COMMANDS

def get_network_interfaces():
    try:
        interfaces = get_if_list()
        active_interfaces = []
        for iface in interfaces:
            try:
                ip = get_if_addr(iface)
                if ip and ip != '127.0.0.1' and ip != '0.0.0.0':
                    active_interfaces.append(iface)
            except:
                continue
        return active_interfaces if active_interfaces else interfaces
    except:
        return ['auto']

def get_interface_info(ifname):
    try:
        ip_addr = get_if_addr(ifname)
        hw_addr = get_if_hwaddr(ifname)
        return ip_addr, hw_addr
    except Exception as e:
        logging.error(f"Failed to get interface info for {ifname}: {e}")
        return None, None

def calculate_broadcast_addr(ip_addr, netmask="255.255.255.0"):
    try:
        import ipaddress
        network = ipaddress.IPv4Network(f"{ip_addr}/{netmask}", strict=False)
        return str(network.broadcast_address)
    except:
        ip_parts = ip_addr.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.255"

class WnbNetatCmd:
    def __init__(self, cmd, dest, src, data=b''):
        self.cmd = cmd
        self.len = struct.pack('!H', len(data))
        self.dest = dest
        self.src = src
        self.data = data

    def to_bytes(self):
        return struct.pack('!B2s6s6s', self.cmd, self.len, self.dest, self.src) + self.data

    @classmethod
    def from_bytes(cls, data):
        if len(data) < 15:
            raise ValueError("Data too short for WnbNetatCmd")
        cmd, length, dest, src = struct.unpack('!B2s6s6s', data[:15])
        payload = data[15:]
        return cls(cmd, dest, src, payload)

class ScapyNetAtMgr:
    def __init__(self, ifname, port=NETAT_PORT, debug=False, scan_timeout=5, response_timeout=3, log_responses=False, log_file="responses.log"):
        self.ifname = ifname
        self.port = port
        self.debug = debug
        self.scan_timeout = scan_timeout
        self.response_timeout = response_timeout
        self.dest = b'\xff\xff\xff\xff\xff\xff'
        self.cookie = self.random_bytes(6)
        self.interface_ip = None
        self.interface_mac = None
        self.broadcast_ip = "255.255.255.255"
        self.debug_mode = False  # Add debug mode flag
        
        # Response logging configuration
        self.log_responses = log_responses
        self.log_file = log_file
        self.response_logger = None
        
        if self.log_responses:
            self.setup_response_logging()
        
        self.init_interface()
        
        self.stop_capture = threading.Event()
        self.captured_packets = []
        self.capture_thread = None

    def init_interface(self):
        if self.ifname == 'auto':
            interfaces = get_network_interfaces()
            if interfaces:
                self.ifname = interfaces[0]
                print(f"Auto-selected interface: {self.ifname}")
            else:
                raise RuntimeError("No suitable network interface found")
        
        self.interface_ip, self.interface_mac = get_interface_info(self.ifname)
        
        if self.interface_ip:
            self.broadcast_ip = calculate_broadcast_addr(self.interface_ip)
            if self.debug:
                print(f"Interface: {self.ifname}")
                print(f"  IP: {self.interface_ip}")
                print(f"  MAC: {self.interface_mac}")
                print(f"  Broadcast: {self.broadcast_ip}")
        else:
            print(f"Warning: Could not get IP for interface {self.ifname}")

    def random_bytes(self, length):
        return bytes([random.randint(0, 255) for _ in range(length)])
    
    def setup_response_logging(self):
        if self.log_file == "responses.log":
            self.log_file = self.generate_log_filename()
            
        self.response_logger = logging.getLogger('response_logger')
        self.response_logger.setLevel(logging.INFO)
        
        for handler in self.response_logger.handlers[:]:
            self.response_logger.removeHandler(handler)
        
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        self.response_logger.addHandler(file_handler)
        self.response_logger.propagate = False
        
    def generate_log_filename(self):
        """Generate automatic log filename with device ID and date"""
        from datetime import datetime
        
        if self.dest == b'\xff\xff\xff\xff\xff\xff':
            device_id = "unknown"
        else:
            device_id = ''.join(f'{b:02x}' for b in self.dest)
            
        date_str = datetime.now().strftime('%Y%m%d')
        
        filename = f"{device_id}-responses-{date_str}.log"
        return filename
        
    def log_response(self, command, response, device_mac=None):
        if self.response_logger:
            device_info = f" from {device_mac}" if device_mac else ""
            self.response_logger.info(f"CMD: {command}{device_info} | RESP: {response}")
            
            for handler in self.response_logger.handlers:
                handler.flush()
    
    def toggle_response_logging(self, enable=None, log_file=None):
        if enable is not None:
            self.log_responses = enable
        else:
            self.log_responses = not self.log_responses
            
        if log_file:
            self.log_file = log_file
        elif self.log_responses and not log_file:
            self.log_file = self.generate_log_filename()
            
        if self.log_responses and not self.response_logger:
            self.setup_response_logging()
        elif not self.log_responses and self.response_logger:
            for handler in self.response_logger.handlers[:]:
                self.response_logger.removeHandler(handler)
            self.response_logger = None
            
        return self.log_responses
        
    def update_log_filename_for_device(self):
        if self.log_responses and self.response_logger:
            new_filename = self.generate_log_filename()
            
            if new_filename != self.log_file:
                for handler in self.response_logger.handlers[:]:
                    handler.close()
                    self.response_logger.removeHandler(handler)
                
                old_filename = self.log_file
                self.log_file = new_filename
                self.setup_response_logging()
                
                self.response_logger.info(f"Log file changed from {old_filename} to {new_filename}")
                
                return new_filename
        return self.log_file

    def start_packet_capture(self):
        if self.capture_thread and self.capture_thread.is_alive():
            return
            
        self.stop_capture.clear()
        self.captured_packets = []
        
        def capture_worker():
            try:
                bpf_filter = f"udp and (port {self.port} or port {NETLOG_PORT})"
                if self.debug:
                    print(f"Starting packet capture on {self.ifname}")
                    print(f"  Filter: {bpf_filter}")
                    print(f"  Looking for packets to/from this host")
                
                def packet_handler(packet):
                    if self.stop_capture.is_set():
                        return True
                    
                    if packet.haslayer(UDP):
                        udp_layer = packet[UDP]
                        if udp_layer.dport == self.port or udp_layer.sport == self.port or \
                           udp_layer.dport == NETLOG_PORT or udp_layer.sport == NETLOG_PORT:
                            self.captured_packets.append(packet)
                            if self.debug:
                                src_ip = packet[IP].src if packet.haslayer(IP) else "unknown"
                                print(f"Captured: {len(udp_layer.payload)} bytes from {src_ip}:{udp_layer.sport}")
                
                sniff(iface=self.ifname, filter=bpf_filter, prn=packet_handler, 
                      stop_filter=lambda p: self.stop_capture.is_set(), timeout=0.5)
                      
            except Exception as e:
                if self.debug:
                    print(f"Packet capture error: {e}")
                    print("This may be normal - some systems require sudo for packet capture")
                logging.error(f"Packet capture error: {e}")
        
        self.capture_thread = threading.Thread(target=capture_worker, daemon=True)
        self.capture_thread.start()
        time.sleep(0.2)

    def stop_packet_capture(self):
        self.stop_capture.set()
        if self.capture_thread:
            self.capture_thread.join(timeout=2)

    def send_packet(self, data, dest_ip=None, dest_mac=None, unicast=False):
        if unicast and dest_mac is None:
            if self.dest != b'\xff\xff\xff\xff\xff\xff':
                dest_mac = ':'.join(f'{b:02x}' for b in self.dest)
            else:
                dest_mac = "ff:ff:ff:ff:ff:ff"
        elif not unicast:
            dest_mac = "ff:ff:ff:ff:ff:ff"
            
        if not dest_ip:
            dest_ip = self.broadcast_ip if not unicast else self.interface_ip
        
        try:
            eth_frame = Ether(dst=dest_mac, src=self.interface_mac) / IP(dst=dest_ip) / UDP(sport=self.port, dport=self.port) / Raw(load=data)
            
            if self.debug:
                transmission_type = "unicast" if unicast else "broadcast"
                print(f"Sending {transmission_type} frame via {self.ifname}")
                print(f"  Ethernet: {self.interface_mac} -> {dest_mac}")
                print(f"  IP: {self.interface_ip} -> {dest_ip}")
                print(f"  Data: {len(data)} bytes")
            
            sendp(eth_frame, iface=self.ifname, verbose=0)
            
            if self.debug:
                print(f" Frame sent successfully")
                
        except Exception as e:
            print(f"Failed to send packet: {e}")
            logging.error(f"Failed to send packet: {e}")
            raise e

    def netat_scan(self, retries=3, retry_delay=0.5):
        self.cookie = self.random_bytes(6)
        scan_cmd = WnbNetatCmd(WNB_NETAT_CMD_SCAN_REQ, b'\xff\xff\xff\xff\xff\xff', self.cookie)
        packet_data = scan_cmd.to_bytes()
        
        if self.debug:
            print(f"Sending NETAT scan request (broadcast - timeout: {self.scan_timeout}s)")
            print(f"  Cookie: {':'.join(f'{b:02x}' for b in self.cookie)}")
        
        for i in range(retries):
            self.send_packet(packet_data, unicast=False)  
            if i < retries - 1:
                time.sleep(retry_delay)
        
        logging.info(f"Sent NETAT scan request with {retries} retries")

    def netat_send(self, atcmd, retries=2, retry_delay=0.2):
        self.captured_packets.clear()
        
        cmd = WnbNetatCmd(WNB_NETAT_CMD_AT_REQ, self.dest, self.cookie, atcmd.encode())
        packet_data = cmd.to_bytes()
        
        is_unicast = True 
        
        if self.debug:
            target_device = ':'.join(f'{b:02x}' for b in self.dest)
            print(f"Sending AT command: {atcmd} (unicast to {target_device})")
            print(f"  Timeout: {self.response_timeout}s")
        
        for i in range(retries):
            self.send_packet(packet_data, unicast=is_unicast)
            if i < retries - 1:
                time.sleep(retry_delay)
        
        logging.info(f"Sent NETAT command: {atcmd} (unicast) with {retries} retries")

    def wait_for_responses(self, timeout_seconds=None, early_exit_for_commands=False, selected_device_only=True):
        if timeout_seconds is None:
            timeout_seconds = self.response_timeout
            
        devices = []
        responses = []
        selected_device_mac = self.dest.hex() if selected_device_only else None
        
        start_time = time.time()
        last_activity = start_time
        check_interval = 0.1
        no_activity_timeout = 1.0
        
        if self.debug:
            if selected_device_only and selected_device_mac:
                target_device = ':'.join(selected_device_mac[i:i+2] for i in range(0, len(selected_device_mac), 2))
                print(f"Waiting for responses from selected device only: {target_device}")
                print(f"  Selected device MAC (hex): {selected_device_mac}")
            else:
                print(f"Waiting for responses from any device (scan mode)")
        
        while time.time() - start_time < timeout_seconds:
            time.sleep(check_interval)
            
            packets_before = len(self.captured_packets)
            packets_processed_this_cycle = 0
            
            for packet in self.captured_packets[:]:
                try:
                    if packet.haslayer(UDP) and packet[UDP].dport == self.port:
                        payload = bytes(packet[UDP].payload)
                        
                        if self.debug:
                            print(f"Processing packet: {len(payload)} bytes from {packet[IP].src}")
                            print(f"  Payload: {payload.hex()}")
                        
                        try:
                            cmd = WnbNetatCmd.from_bytes(payload)
                            
                            if self.debug:
                                print(f"  Parsed command: {cmd.cmd}")
                                print(f"  Dest: {cmd.dest.hex()}")
                                print(f"  Our cookie: {self.cookie.hex()}")
                            
                            if cmd.dest == self.cookie:
                                device_mac = cmd.src.hex()
                                
                                if self.debug:
                                    device_display = ':'.join(device_mac[i:i+2] for i in range(0, len(device_mac), 2))
                                    print(f"  Response from device: {device_display} (hex: {device_mac})")
                                    if selected_device_only and selected_device_mac:
                                        print(f"  Expected device: {selected_device_mac}")
                                        print(f"  Match: {device_mac == selected_device_mac}")
                                
                                if selected_device_only and selected_device_mac and device_mac != selected_device_mac:
                                    if self.debug:
                                        other_device = ':'.join(device_mac[i:i+2] for i in range(0, len(device_mac), 2))
                                        print(f" Ignoring response from non-selected device: {other_device}")
                                    self.captured_packets.remove(packet)
                                    continue
                                
                                if self.debug and selected_device_only:
                                    print(f" Processing response from selected device")
                                
                                last_activity = time.time()
                                packets_processed_this_cycle += 1
                                
                                if cmd.cmd == WNB_NETAT_CMD_SCAN_RESP:
                                    if cmd.src not in devices:
                                        devices.append(cmd.src)
                                        device_mac = ':'.join(f'{b:02x}' for b in cmd.src)
                                        print(f"Found device: {device_mac}")
                                        logging.info(f"Discovered device: {device_mac}")
                                elif cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                                    response_text = cmd.data.decode('utf-8', errors='ignore')
                                    if response_text and response_text not in responses:
                                        responses.append(response_text)
                                        if self.debug:
                                            print(f"  Got AT response: {response_text[:50]}...")
                        except Exception as e:
                            if self.debug:
                                print(f"  Failed to parse as WnbNetatCmd: {e}")
                        
                        self.captured_packets.remove(packet)
                        
                except Exception as e:
                    if self.debug:
                        print(f"Error processing packet: {e}")
            
            if early_exit_for_commands and responses:
                time_since_activity = time.time() - last_activity
                if time_since_activity > no_activity_timeout:
                    if self.debug:
                        print(f"Early exit: No activity for {time_since_activity:.1f}s after getting responses")
                    break
            
            if not (early_exit_for_commands and responses):
                elapsed = time.time() - start_time
                if elapsed > 2 and int(elapsed) % 2 == 0 and elapsed - int(elapsed) < check_interval:
                    remaining = timeout_seconds - elapsed
                    if remaining > 0:
                        print(f"  Still waiting... {remaining:.0f}s remaining")
        
        if self.debug:
            elapsed = time.time() - start_time
            print(f"Response wait completed after {elapsed:.1f}s")
            print(f"Found {len(devices)} devices, {len(responses)} responses")
        
        return devices, responses

class CursesInterface:
    def __init__(self, mgr):
        if not HAS_CURSES:
            raise ImportError("Curses not available on this platform")
            
        self.mgr = mgr
        self.stdscr = None
        self.history = []
        self.history_pos = 0
        self.current_command = ""
        self.cursor_pos = 0
        self.output_lines = []
        self.max_output_lines = 100
        self.running = True
        self.blink_state = True
        self.last_blink = time.time()
        
        self.waiting_for_response = False
        self.wait_start_time = 0
        self.wait_operation = ""
        self.wait_timeout = 0
        self.wait_spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.wait_spinner_pos = 0
        self.last_spinner_update = time.time()
        self.operation_cancelled = False
        self.active_response_threads = []
        
        self.signal_graph_active = False
        self.signal_graph_interval = 5.0
        self.signal_history = []
        self.max_signal_history = 50
        
        self.setup_output_capture()
        
    def setup_output_capture(self):
        import sys
        from io import StringIO
        
        self.original_stdout = sys.stdout
        
        class GUICapture:
            def __init__(self, gui):
                self.gui = gui
                self.buffer = ""
                
            def write(self, text):
                if text.strip():
                    problematic_messages = [
                        "Still waiting...", "Processing packet", "Waiting for", 
                        "Captured:", "Parsed command:", "Response from device:",
                        "Expected device:", "Match:", "Our cookie:", "Payload:",
                        "Starting packet capture", "Packet capture error", "Frame sent"
                    ]
                    if not any(msg in text for msg in problematic_messages):
                        clean_text = str(text).replace('\x00', '').replace('\r', '').replace('\n', ' ')
                        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\t'])
                        if clean_text.strip(): 
                            import threading
                            def add_line_async():
                                try:
                                    self.gui.add_output_line(clean_text.strip(), 5)
                                except:
                                    pass
                            threading.Thread(target=add_line_async, daemon=True).start()
                return len(text)
                
            def flush(self):
                pass
                
        self.gui_capture = GUICapture(self)
        
    def start_wait_feedback(self, operation, timeout):
        self.operation_cancelled = False
        self.waiting_for_response = True
        self.wait_start_time = time.time()
        self.wait_operation = operation
        self.wait_timeout = timeout
        self.wait_spinner_pos = 0
        self.last_spinner_update = time.time()
        
    def stop_wait_feedback(self):
        self.waiting_for_response = False
        self.wait_operation = ""
        
    def cancel_operation(self):
        self.operation_cancelled = True
        
        try:
            self.mgr.stop_packet_capture()
        except:
            pass
        
        try:
            self.stop_output_capture()
        except:
            pass
            
        if self.signal_graph_active:
            self.stop_signal_graph()
            
        time.sleep(0.1)
        
        active_threads = getattr(self, 'active_response_threads', [])
        for thread in active_threads[:]:
            if thread.is_alive():
                thread.join(timeout=0.5)
                if thread in active_threads:
                    active_threads.remove(thread)
        
        self.active_response_threads = []
        self.stop_wait_feedback()
        
        self.operation_cancelled = False
        
        self.add_output_line("Operation cancelled by user", 2)
        
    def update_wait_spinner(self):
        current_time = time.time()
        if current_time - self.last_spinner_update > 0.08:
            self.wait_spinner_pos = (self.wait_spinner_pos + 1) % len(self.wait_spinner)
            self.last_spinner_update = current_time
            
    def get_wait_status_line(self):
        if not self.waiting_for_response:
            return ""
            
        elapsed = time.time() - self.wait_start_time
        
        max_elapsed = self.wait_timeout * 2
        if elapsed > max_elapsed:
            self.stop_wait_feedback()
            return ""
            
        remaining = max(0, self.wait_timeout - elapsed)
        
        self.update_wait_spinner()
        spinner = self.wait_spinner[self.wait_spinner_pos]
        
        progress_width = 20
        if self.wait_timeout > 0:
            progress = min(1.0, elapsed / self.wait_timeout)
            filled = int(progress * progress_width)
            bar = "█" * filled + "░" * (progress_width - filled)
            percentage = int(progress * 100)
        else:
            bar = "█" * progress_width
            percentage = 100
            
        elapsed_str = f"{elapsed:.1f}s"
        remaining_str = f"{remaining:.1f}s" if remaining > 0 else "timeout"
        
        status = f"{spinner} {self.wait_operation} [{bar}] {percentage}% | {elapsed_str} elapsed | {remaining_str} left"
        
        return status
        
    def start_output_capture(self):
        import sys
        sys.stdout = self.gui_capture
        
    def stop_output_capture(self):
        import sys
        sys.stdout = self.original_stdout
        
    def init_curses(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        curses.curs_set(0)
        
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            
    def cleanup_curses(self):
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            
    def add_output_line(self, text, color_pair=5):
        timestamp = datetime.now().strftime("%H:%M:%S")
        clean_text = str(text).replace('\x00', '').replace('\r', '').replace('\n', ' ')
        clean_text = ''.join(char for char in clean_text if ord(char) >= 32 or char in ['\t'])
        self.output_lines.append((f"[{timestamp}] {clean_text}", color_pair))
        if len(self.output_lines) > self.max_output_lines:
            self.output_lines.pop(0)
            
    def get_completions(self, text):
        base_commands = ["exit", "scan", "device", "deviceinfo", "help", "show_config", "clear", "debug_mode", "production_mode", "debug", "logging", "signalgraph"]
        arg_commands = ["setmac", "loadconfig", "saveconfig", "signalgraph_interval"]
        
        available_set_commands = SET_COMMANDS if self.mgr.debug_mode else PRODUCTION_SET_COMMANDS
        available_get_commands = GET_COMMANDS if self.mgr.debug_mode else PRODUCTION_GET_COMMANDS
        
        at_set_commands = [f"at+{cmd}=" for cmd in available_set_commands]
        at_get_commands = [f"at+{cmd}?" for cmd in available_get_commands]
        at_commands = ["at+"] + at_set_commands + at_get_commands
        
        all_commands = base_commands + arg_commands + at_commands
        
        matches = [cmd for cmd in all_commands if cmd.lower().startswith(text.lower())]
        return matches
        
    def handle_tab_completion(self):
        if not self.current_command:
            return
            
        words = self.current_command[:self.cursor_pos].split()
        if not words:
            return
            
        current_word = words[-1] if words else ""
        completions = self.get_completions(current_word)
        
        if len(completions) == 1:
            completion = completions[0]
            if words:
                new_cmd = " ".join(words[:-1]) + " " + completion if len(words) > 1 else completion
            else:
                new_cmd = completion
            self.current_command = new_cmd + " "
            self.cursor_pos = len(self.current_command)
        elif len(completions) > 1:
            self.add_output_line(f"Completions: {', '.join(completions)}", 4)
            
    def draw_screen(self):
        if not self.stdscr:
            return
            
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        debug_indicator = " [DEBUG MODE]" if self.mgr.debug_mode else ""
        title = f"Taixin LibNetat Tool - nCurses GUI ({platform.system()}){debug_indicator}"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.color_pair(1) | curses.A_BOLD)
        
        device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
        device_info = f"Device: {device_mac} | Interface: {self.mgr.ifname} | Timeouts: {self.mgr.scan_timeout}s/{self.mgr.response_timeout}s"
        if len(device_info) > width - 4:
            device_info = device_info[:width-7] + "..."
        self.stdscr.addstr(1, 2, device_info, curses.color_pair(4))
        
        line_offset = 0
        if self.waiting_for_response:
            wait_status = self.get_wait_status_line()
            if len(wait_status) > width - 4:
                wait_status = wait_status[:width-7] + "..."
            self.stdscr.addstr(2, 2, wait_status, curses.color_pair(6) | curses.A_BOLD)
            line_offset = 1
            
        separator_line = 2 + line_offset
        self.stdscr.addstr(separator_line, 0, "─" * width, curses.color_pair(5))
        
        output_start = separator_line + 1
        prompt_lines = 3
        available_lines = height - output_start - prompt_lines - 1
        
        display_lines = self.output_lines[-available_lines:] if len(self.output_lines) > available_lines else self.output_lines
        
        for i, (line, color) in enumerate(display_lines):
            if output_start + i < height - prompt_lines - 1:
                safe_line = str(line).replace('\x00', '').replace('\r', '').replace('\n', ' ')
                safe_line = ''.join(char for char in safe_line if ord(char) >= 32 or char in ['\t'])
                display_line = safe_line[:width-1] if len(safe_line) >= width else safe_line
                try:
                    self.stdscr.addstr(output_start + i, 0, display_line, curses.color_pair(color))
                except ValueError as e:
                    fallback = f"[Display Error: {str(e)[:30]}...]"
                    self.stdscr.addstr(output_start + i, 0, fallback, curses.color_pair(3))
                
        prompt_y = height - prompt_lines - 1
        self.stdscr.addstr(prompt_y, 0, "─" * width, curses.color_pair(5))
        
        prompt = "netat> "
        self.stdscr.addstr(prompt_y + 1, 0, prompt, curses.color_pair(2) | curses.A_BOLD)
        
        cmd_start_x = len(prompt)
        cmd_display = self.current_command[:width - cmd_start_x - 1] if len(self.current_command) >= width - cmd_start_x else self.current_command
        self.stdscr.addstr(prompt_y + 1, cmd_start_x, cmd_display, curses.color_pair(5))
        
        cursor_x = cmd_start_x + min(self.cursor_pos, len(cmd_display))
        if cursor_x < width - 1:
            current_time = time.time()
            if current_time - self.last_blink > 0.5:
                self.blink_state = not self.blink_state
                self.last_blink = current_time
                
            if self.blink_state:
                cursor_char = cmd_display[self.cursor_pos] if self.cursor_pos < len(cmd_display) else " "
                self.stdscr.addstr(prompt_y + 1, cursor_x, cursor_char, curses.color_pair(2) | curses.A_REVERSE)
                
        help_text = "TAB: complete | UP/DOWN: history | CTRL+C: exit/cancel | 'debug': toggle debug mode"
        if self.waiting_for_response:
            help_text = "Waiting for device response... | CTRL+C: cancel"
            
        if len(help_text) < width:
            self.stdscr.addstr(height - 1, 0, help_text, curses.color_pair(4))
            
        self.stdscr.refresh()
        
    def execute_command(self, command):
        cmd = command.strip().lower()
        
        if cmd == "exit":
            self.running = False
            return
        elif cmd == "clear":
            self.output_lines = []
            return
        elif cmd == "scan":
            self.execute_scan_command()
            return
        elif cmd == "device":
            device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
            self.add_output_line(f"Device: {device_mac}, Interface: {self.mgr.ifname}", 4)
            return
        elif cmd == "debug" or cmd == "debug_mode":
            self.mgr.debug_mode = not self.mgr.debug_mode
            mode_text = "enabled" if self.mgr.debug_mode else "disabled"
            self.add_output_line(f"Debug mode {mode_text}", 1 if self.mgr.debug_mode else 2)
            commands_count = len(SET_COMMANDS) + len(GET_COMMANDS) if self.mgr.debug_mode else len(PRODUCTION_SET_COMMANDS) + len(PRODUCTION_GET_COMMANDS)
            self.add_output_line(f"Available commands: {commands_count}", 4)
            return
        elif cmd == "production_mode":
            self.mgr.debug_mode = False
            self.add_output_line("Production mode enabled (debug commands disabled)", 2)
            return
        elif cmd == "logging":
            status = self.mgr.toggle_response_logging()
            status_text = "enabled" if status else "disabled"
            log_file = self.mgr.log_file if status else "N/A"
            self.add_output_line(f"Response logging {status_text} (file: {log_file})", 1 if status else 2)
            return
        elif cmd.startswith("signalgraph_interval"):
            try:
                parts = command.split(None, 1)
                if len(parts) > 1:
                    interval = float(parts[1])
                    if 1.0 <= interval <= 60.0:
                        self.signal_graph_interval = interval
                        self.add_output_line(f"Signal graph interval set to {interval}s", 1)
                    else:
                        self.add_output_line("Interval must be between 1.0 and 60.0 seconds", 3)
                else:
                    self.add_output_line(f"Current interval: {self.signal_graph_interval}s", 4)
            except ValueError:
                self.add_output_line("Usage: signalgraph_interval <seconds>", 3)
            return
        elif cmd == "signalgraph":
            if self.signal_graph_active:
                self.stop_signal_graph()
            else:
                self.start_signal_graph()
            return
        elif cmd.startswith("setmac"):
            try:
                _, mac_str = command.split(None, 1)
                self.mgr.dest = self.parse_mac_address(mac_str)
                device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
                self.add_output_line(f"Device set to: {device_mac}", 1)
                
                if self.mgr.log_responses:
                    new_filename = self.mgr.update_log_filename_for_device()
                    self.add_output_line(f"Log file updated: {new_filename}", 4)
            except:
                self.add_output_line("Usage: setmac XX:XX:XX:XX:XX:XX", 3)
            return
        elif cmd == "help":
            self.show_help()
            return
        elif cmd.startswith("at"):
            self.send_at_command(command)
            return
        elif cmd == "deviceinfo":
            self.send_device_info_commands()
            return
        elif cmd.startswith("loadconfig"):
            try:
                parts = command.split(None, 1)
                if len(parts) > 1:
                    filename = parts[1]
                    self.load_config_file(filename)
                else:
                    self.add_output_line("Usage: loadconfig <filename>", 3)
            except Exception as e:
                self.add_output_line(f"Error loading config: {e}", 3)
            return
        elif cmd.startswith("saveconfig"):
            try:
                parts = command.split(None, 1)
                filename = parts[1] if len(parts) > 1 else "device_config.txt"
                self.save_config_file(filename)
            except Exception as e:
                self.add_output_line(f"Error saving config: {e}", 3)
            return
        else:
            if cmd.strip():
                self.add_output_line(f"Unknown command: {command}", 3)
                self.add_output_line("Type 'help' for available commands", 4)
                
    def execute_scan_command(self):
        self.add_output_line("Starting device scan...", 4)
        
        self.start_wait_feedback("Scanning for devices", self.mgr.scan_timeout)
        
        scan_devices = []
        scan_error = [None]
        scan_sent = [False]
        
        def send_scan_thread():
            try:
                self.start_output_capture()
                self.mgr.start_packet_capture()
                self.mgr.netat_scan()
                scan_sent[0] = True
                
            except Exception as e:
                scan_error[0] = str(e)
        
        scan_thread = threading.Thread(target=send_scan_thread, daemon=True)
        scan_thread.start()
        
        scan_thread.join(timeout=1.0)
        
        if scan_error[0]:
            self.stop_wait_feedback()
            self.add_output_line(f"✗ Scan failed: {scan_error[0]}", 3)
            return
        
        if not scan_sent[0]:
            self.stop_wait_feedback()
            self.add_output_line("✗ Scan send timeout", 3)
            return
        
        self.start_device_collection(scan_devices)
        
    def start_device_collection(self, device_list):
        """Start collecting scan responses in a non-blocking way"""
        def collect_devices():
            start_time = time.time()
            timeout = self.mgr.scan_timeout
            
            while (time.time() - start_time) < timeout:
                if self.operation_cancelled:
                    break
                    
                new_devices = []
                for packet in self.mgr.captured_packets[:]:
                    try:
                        if packet.haslayer(UDP) and packet[UDP].dport == self.mgr.port:
                            payload = bytes(packet[UDP].payload)
                            cmd = WnbNetatCmd.from_bytes(payload)
                            
                            if cmd.dest == self.mgr.cookie and cmd.cmd == WNB_NETAT_CMD_SCAN_RESP:
                                if cmd.src not in device_list:
                                    device_list.append(cmd.src)
                                    new_devices.append(cmd.src)
                                    device_mac = ':'.join(f'{b:02x}' for b in cmd.src)
                                    self.add_output_line(f"Found device: {device_mac}", 1)
                        
                        self.mgr.captured_packets.remove(packet)
                    except:
                        continue
                
                time.sleep(0.1)
            
            # Cleanup
            try:
                self.mgr.stop_packet_capture()
            except:
                pass
            self.stop_output_capture()
            
            # Process results
            if device_list:
                self.add_output_line(f"Found {len(device_list)} device(s) total", 1)
                self.mgr.dest = device_list[0]
                device_mac = ':'.join(f'{b:02x}' for b in device_list[0])
                self.add_output_line(f"Auto-selected: {device_mac}", 1)
                
                if self.mgr.log_responses:
                    new_filename = self.mgr.update_log_filename_for_device()
                    self.add_output_line(f"Log file updated: {new_filename}", 4)
            else:
                self.add_output_line("No devices found", 3)
            
            self.stop_wait_feedback()
        
        device_thread = threading.Thread(target=collect_devices, daemon=True)
        device_thread.start()
            
    def send_at_command(self, command):
        self.add_output_line(f"Sending: {command}", 4)
        
        operation_name = f"AT Command: {command[:20]}..."
        self.start_wait_feedback(operation_name, self.mgr.response_timeout)
        
        import threading
        command_responses = []
        command_error = [None]
        command_sent = [False]
        
        def send_command_thread():
            try:
                self.start_output_capture()
                self.mgr.start_packet_capture()
                self.mgr.netat_send(command)
                command_sent[0] = True
                
            except Exception as e:
                command_error[0] = str(e)
        
        command_thread = threading.Thread(target=send_command_thread, daemon=True)
        command_thread.start()
        
        command_thread.join(timeout=1.0)
        
        if command_error[0]:
            self.stop_wait_feedback()
            self.add_output_line(f"✗ Command failed: {command_error[0]}", 3)
            return
        
        if not command_sent[0]:
            self.stop_wait_feedback()
            self.add_output_line("✗ Command send timeout", 3)
            return
        
        self.start_response_collection(command_responses, command)
        
    def start_response_collection(self, response_list, command="unknown"):
        """Start collecting responses in a non-blocking way"""
        import threading
        
        def collect_responses():
            start_time = time.time()
            timeout = min(self.mgr.response_timeout, 3)
            check_interval = 0.05 
            
            while (time.time() - start_time) < timeout and not self.operation_cancelled:
                new_responses = []
                try:
                    for packet in self.mgr.captured_packets[:]:
                        try:
                            if packet.haslayer(UDP) and packet[UDP].dport == self.mgr.port:
                                payload = bytes(packet[UDP].payload)
                                cmd = WnbNetatCmd.from_bytes(payload)
                                
                                if cmd.dest == self.mgr.cookie and cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                                    response_text = cmd.data.decode('utf-8', errors='ignore')
                                    if response_text and response_text not in new_responses:
                                        new_responses.append(response_text)
                                        response_list.append(response_text)
                            
                            self.mgr.captured_packets.remove(packet)
                        except:
                            continue
                except:
                    pass
                
                if new_responses:
                    break
                    
                if self.operation_cancelled:
                    break
                    
                time.sleep(check_interval)
            
            try:
                self.mgr.stop_packet_capture()
            except:
                pass
            self.stop_output_capture()
            
            if not self.operation_cancelled:
                if response_list:
                    combined_response = parse_at_response(response_list)
                    
                    if self.mgr.log_responses:
                        device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
                        self.mgr.log_response(command, combined_response, device_mac)
                    
                    if len(combined_response) > 80:
                        lines = combined_response.split('\n') if '\n' in combined_response else [combined_response[i:i+80] for i in range(0, len(combined_response), 80)]
                        for line in lines:
                            self.add_output_line(f"Response: {line}", 1)
                    else:
                        self.add_output_line(f"Response: {combined_response}", 1)
                else:
                    self.add_output_line("No response received", 3)
            
            self.stop_wait_feedback()
        
        response_thread = threading.Thread(target=collect_responses, daemon=True)
        response_thread.start()
        
        self.active_response_threads.append(response_thread)
            
    def send_device_info_commands(self):
        info_commands = ["at+ssid?", "at+mode?", "at+keymgmt?", "at+psk?", "at+bss_bw?", "at+chan_list?"]
        
        self.add_output_line("Getting device information...", 4)
        
        total_commands = len(info_commands)
        self.start_wait_feedback(f"Device Info: 0/{total_commands} queries", total_commands * self.mgr.response_timeout)
        
        completed_commands = 0
        
        for i, cmd in enumerate(info_commands):
            if self.operation_cancelled:
                break
            
            self.wait_operation = f"Device Info: {i+1}/{total_commands} - {cmd.replace('at+', '').replace('?', '').upper()}"
            
            cmd_responses = []
            cmd_error = [None]
            cmd_sent = [False]
            
            def send_cmd_thread():
                try:
                    self.start_output_capture()
                    self.mgr.start_packet_capture()
                    self.mgr.netat_send(cmd)
                    cmd_sent[0] = True
                    
                except Exception as e:
                    cmd_error[0] = str(e)
            
            cmd_thread = threading.Thread(target=send_cmd_thread, daemon=True)
            cmd_thread.start()
            
            cmd_thread.join(timeout=1.0)
            
            if cmd_error[0]:
                param_name = cmd.replace("at+", "").replace("?", "").upper()
                self.add_output_line(f"{param_name}: Error - {cmd_error[0]}", 3)
                continue
            
            if not cmd_sent[0]:
                param_name = cmd.replace("at+", "").replace("?", "").upper()
                self.add_output_line(f"{param_name}: Send timeout", 3)
                continue
            
            self.start_single_response_collection(cmd_responses, cmd, i+1, total_commands)
            
            max_wait = self.mgr.response_timeout
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait and not self.operation_cancelled:
                if cmd_responses: 
                    break
                time.sleep(0.1)
            
            if cmd_responses and not self.operation_cancelled:
                combined_response = parse_at_response(cmd_responses)
                param_name = cmd.replace("at+", "").replace("?", "").upper()
                self.add_output_line(f"{param_name}: {combined_response}", 1)
                
                if self.mgr.log_responses:
                    device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
                    self.mgr.log_response(cmd, combined_response, device_mac)
                    
                completed_commands += 1
            elif not self.operation_cancelled:
                param_name = cmd.replace("at+", "").replace("?", "").upper()
                self.add_output_line(f"{param_name}: No response", 3)
            
            try:
                self.mgr.stop_packet_capture()
            except:
                pass
            self.stop_output_capture()
            
            if self.operation_cancelled:
                self.add_output_line("Device info query cancelled", 3)
                break
                
            time.sleep(0.1)
        
        self.stop_wait_feedback()
        
        if not self.operation_cancelled:
            if completed_commands > 0:
                self.add_output_line(f"Device info complete: {completed_commands}/{total_commands} successful", 1)
            else:
                self.add_output_line("Device info failed: No responses received", 3)
                
    def start_single_response_collection(self, response_list, command, current_cmd, total_cmds):
        import threading
        
        def collect_single_response():
            start_time = time.time()
            timeout = min(self.mgr.response_timeout, 3)
            check_interval = 0.05
            
            while (time.time() - start_time) < timeout and not self.operation_cancelled:
                # Check for new packets
                new_responses = []
                try:
                    for packet in self.mgr.captured_packets[:]:
                        try:
                            if packet.haslayer(UDP) and packet[UDP].dport == self.mgr.port:
                                payload = bytes(packet[UDP].payload)
                                cmd = WnbNetatCmd.from_bytes(payload)
                                
                                if cmd.dest == self.mgr.cookie and cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                                    response_text = cmd.data.decode('utf-8', errors='ignore')
                                    if response_text and response_text not in new_responses:
                                        new_responses.append(response_text)
                                        response_list.append(response_text)
                            
                            self.mgr.captured_packets.remove(packet)
                        except:
                            continue
                except:
                    pass
                
                if new_responses:
                    break
                    
                if self.operation_cancelled:
                    break
                    
                time.sleep(check_interval)
        
        response_thread = threading.Thread(target=collect_single_response, daemon=True)
        response_thread.start()
        
        self.active_response_threads.append(response_thread)
            
    def load_config_file(self, filename):
        try:
            self.add_output_line(f"Loading configuration from: {filename}", 4)
            
            if not os.path.exists(filename):
                self.add_output_line(f"✗ Config file not found: {filename}", 3)
                return
                
            commands_applied = 0
            commands_failed = 0
            
            with open(filename, 'r') as f:
                lines = f.readlines()
                
            self.add_output_line(f"Found {len(lines)} lines in config file", 4)
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                    
                if '=' in line:
                    param, value = line.split('=', 1)
                    param = param.strip()
                    value = value.strip()
                    
                    at_command = f"at+{param}={value}"
                    
                    operation_name = f"Setting {param.upper()}"
                    self.start_wait_feedback(operation_name, self.mgr.response_timeout)
                    
                    self.start_output_capture()
                    self.mgr.start_packet_capture()
                    self.mgr.netat_send(at_command)
                    
                    devices, responses = self.mgr.wait_for_responses(
                        timeout_seconds=self.mgr.response_timeout, 
                        early_exit_for_commands=True
                    )
                    
                    self.mgr.stop_packet_capture()
                    self.stop_output_capture()
                    self.stop_wait_feedback()
                    
                    if responses:
                        combined_response = parse_at_response(responses)
                        if "OK" in combined_response or combined_response.strip():
                            self.add_output_line(f"✓ {param} set successfully", 1)
                            commands_applied += 1
                        else:
                            self.add_output_line(f"✗ {param} failed: {combined_response}", 3)
                            commands_failed += 1
                    else:
                        self.add_output_line(f"✗ {param} failed: No response", 3)
                        commands_failed += 1
                        
                    time.sleep(0.2)
                else:
                    self.add_output_line(f"Line {line_num}: Invalid format", 3)
                    commands_failed += 1
                    
            total_commands = commands_applied + commands_failed
            self.add_output_line(f"✓ Config complete: {commands_applied}/{total_commands} applied", 
                               1 if commands_failed == 0 else 2)
                                
        except Exception as e:
            self.add_output_line(f"✗ Error loading config: {e}", 3)
            
    def save_config_file(self, filename):
        try:
            self.add_output_line(f"Saving configuration to: {filename}", 4)
            
            config_commands = [
                ("ssid", "at+ssid?"), ("mode", "at+mode?"), ("keymgmt", "at+keymgmt?"),
                ("psk", "at+psk?"), ("bss_bw", "at+bss_bw?"), ("chan_list", "at+chan_list?"),
                ("txpower", "at+txpower?"), ("channel", "at+channel?"), 
                ("country_region", "at+country_region?"), ("beacon_int", "at+beacon_int?"),
                ("dtim_period", "at+dtim_period?")
            ]
            
            config_data = {}
            successful_queries = 0
            
            for i, (param_name, at_cmd) in enumerate(config_commands):
                operation_name = f"Reading {i+1}/{len(config_commands)}: {param_name.upper()}"
                self.start_wait_feedback(operation_name, self.mgr.response_timeout)
                
                self.start_output_capture()
                self.mgr.start_packet_capture()
                self.mgr.netat_send(at_cmd)
                
                devices, responses = self.mgr.wait_for_responses(
                    timeout_seconds=self.mgr.response_timeout, 
                    early_exit_for_commands=True
                )
                
                self.mgr.stop_packet_capture()
                self.stop_output_capture()
                self.stop_wait_feedback()
                
                if responses:
                    combined_response = parse_at_response(responses)
                    if combined_response and combined_response != "ERROR":
                        config_data[param_name] = combined_response
                        successful_queries += 1
                        short_resp = combined_response[:30] + ('...' if len(combined_response) > 30 else '')
                        self.add_output_line(f"✓ {param_name}: {short_resp}", 1)
                    else:
                        self.add_output_line(f"✗ {param_name}: Invalid response", 3)
                else:
                    self.add_output_line(f"{param_name}: No response", 3)
                    
                time.sleep(0.1)
                
            if config_data:
                with open(filename, 'w') as f:
                    f.write(f"# Device Configuration - Saved {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Device MAC: {':'.join(f'{b:02x}' for b in self.mgr.dest)}\n")
                    f.write(f"# Format: parameter=value\n\n")
                    
                    for param, value in config_data.items():
                        f.write(f"{param}={value}\n")
                        
                self.add_output_line(f"✓ Config saved: {successful_queries} parameters → {filename}", 1)
            else:
                self.add_output_line("✗ No config data - cannot save", 3)
                
        except Exception as e:
            self.add_output_line(f"✗ Error saving config: {e}", 3)
            
    def start_signal_graph(self):
        if self.signal_graph_active:
            self.add_output_line("Signal graph already active", 3)
            return
            
        self.signal_graph_active = True
        self.signal_history = []
        self.add_output_line(f"Signal graph started (interval: {self.signal_graph_interval}s)", 1)
        self.add_output_line("Use 'signalgraph' again to stop", 4)
        
        def signal_graph_worker():
            while self.signal_graph_active and self.running:
                if self.operation_cancelled:
                    break
                    
                # Send RSSI query
                rssi_responses = []
                rssi_error = [None]
                
                def get_rssi():
                    try:
                        self.mgr.start_packet_capture()
                        self.mgr.netat_send("at+rssi?")
                        
                        timeout = min(self.mgr.response_timeout, 2)
                        start_time = time.time()
                        
                        while (time.time() - start_time) < timeout:
                            for packet in self.mgr.captured_packets[:]:
                                try:
                                    if packet.haslayer(UDP) and packet[UDP].dport == self.mgr.port:
                                        payload = bytes(packet[UDP].payload)
                                        cmd = WnbNetatCmd.from_bytes(payload)
                                        
                                        if cmd.dest == self.mgr.cookie and cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                                            response_text = cmd.data.decode('utf-8', errors='ignore')
                                            if response_text and response_text not in rssi_responses:
                                                rssi_responses.append(response_text)
                                    
                                    self.mgr.captured_packets.remove(packet)
                                except:
                                    continue
                            
                            if rssi_responses:
                                break
                            time.sleep(0.1)
                                
                    except Exception as e:
                        rssi_error[0] = str(e)
                    finally:
                        try:
                            self.mgr.stop_packet_capture()
                        except:
                            pass
                
                # Get RSSI reading
                rssi_thread = threading.Thread(target=get_rssi, daemon=True)
                rssi_thread.start()
                rssi_thread.join(timeout=3)
                
                if rssi_error[0]:
                    self.add_output_line(f"RSSI query failed: {rssi_error[0]}", 3)
                elif rssi_responses:
                    try:
                        combined_response = parse_at_response(rssi_responses)
                        rssi_value = self.extract_rssi_value(combined_response)
                        
                        if rssi_value is not None:
                            self.signal_history.append(rssi_value)
                            if len(self.signal_history) > self.max_signal_history:
                                self.signal_history.pop(0)
                            
                            if self.mgr.log_responses:
                                device_mac = ':'.join(f'{b:02x}' for b in self.mgr.dest)
                                self.mgr.log_response("at+rssi?", combined_response, device_mac)
                            
                            self.display_signal_graph(rssi_value)
                        else:
                            self.add_output_line(f"Invalid RSSI response: {combined_response}", 3)
                    except Exception as e:
                        self.add_output_line(f"RSSI parse error: {e}", 3)
                else:
                    self.add_output_line("No RSSI response", 3)
                
                for _ in range(int(self.signal_graph_interval * 10)):
                    if not self.signal_graph_active or self.operation_cancelled:
                        break
                    time.sleep(0.1)
            
            self.signal_graph_active = False
        
        signal_thread = threading.Thread(target=signal_graph_worker, daemon=True)
        signal_thread.start()
        
    def stop_signal_graph(self):
        if not self.signal_graph_active:
            self.add_output_line("Signal graph not active", 3)
            return
            
        self.signal_graph_active = False
        self.add_output_line("Signal graph stopped", 2)
        
    def extract_rssi_value(self, response):
        try:
            import re
            numbers = re.findall(r'-?\d+', response)
            for num in numbers:
                value = int(num)
                if -100 <= value <= 0:
                    return value
            return None
        except:
            return None
            
    def display_signal_graph(self, current_rssi):
        if not self.signal_history:
            return
            
        graph_width = 40
        min_rssi = -100
        max_rssi = -20  
        
        graph_line = ""
        history_to_show = self.signal_history[-graph_width:]
        
        for rssi in history_to_show:
            normalized = (rssi - min_rssi) / (max_rssi - min_rssi)
            normalized = max(0, min(1, normalized))  
            
            if normalized >= 0.8:
                graph_line += "█"  
            elif normalized >= 0.6:
                graph_line += "▇"  
            elif normalized >= 0.4:
                graph_line += "▅"  
            elif normalized >= 0.2:
                graph_line += "▃"  
            else:
                graph_line += "▁"  
        
        graph_line = graph_line.ljust(graph_width)
        
        if current_rssi >= -50:
            quality = "Excellent"
            color = 1  # Green
        elif current_rssi >= -60:
            quality = "Good"
            color = 1  # Green
        elif current_rssi >= -70:
            quality = "Fair"
            color = 2  # Yellow
        else:
            quality = "Poor"
            color = 3  # Red
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        graph_display = f"[{timestamp}] RSSI: {current_rssi}dBm ({quality}) [{graph_line}]"
        
        self.add_output_line(graph_display, color)
        
    def parse_mac_address(self, mac_str):
        try:
            return bytes(int(x, 16) for x in mac_str.split(':'))
        except ValueError:
            raise ValueError("Invalid MAC address format")
            
    def show_help(self):
        debug_status = "ENABLED" if self.mgr.debug_mode else "DISABLED"
        help_text = [
            "=== ncurses GUI Commands ===",
            "exit                    - Exit the program",
            "clear                   - Clear output screen", 
            "scan                    - Scan for devices",
            "device                  - Show current device",
            "deviceinfo              - Get device information",
            "setmac <mac>            - Set device MAC",
            "loadconfig <file>       - Load config file",
            "saveconfig [file]       - Save config file",
            f"debug                   - Toggle debug mode (currently {debug_status})",
            "logging                 - Toggle response logging",
            "signalgraph             - Start/stop live RSSI graph",
            "signalgraph_interval <s> - Set graph refresh interval",
            "production_mode         - Disable debug commands",
            "help                    - Show this help",
            "",
            "=== Visual Indicators ===",
            "Animated spinner        - Operation in progress",
            "Progress bar            - Wait progress",
            "Signal graph            - Live RSSI visualization",
            "Status messages         - Success/failure indication",
            "",
            "=== AT Commands ===",
            "at+<cmd>=<value>        - Set parameter",
            "at+<cmd>?               - Get parameter",
            f"Available commands: {len(SET_COMMANDS) + len(GET_COMMANDS) if self.mgr.debug_mode else len(PRODUCTION_SET_COMMANDS) + len(PRODUCTION_GET_COMMANDS)}",
            "",
            "=== Signal Graph ===",
            "signalgraph             - Toggle live RSSI monitoring",
            "signalgraph_interval 3  - Set 3 second refresh rate",
            f"Current interval: {self.signal_graph_interval}s",
            "",
            "=== Navigation ===",
            "TAB                     - Auto-complete",
            "UP/DOWN                 - Command history",
            "CTRL+C                  - Exit/cancel"
        ]
        
        for line in help_text:
            color = 1 if line.startswith("===") else 2 if "debug mode" in line.lower() else 5
            self.add_output_line(line, color)
            
    def run(self):
        try:
            self.init_curses()
            self.add_output_line(f"nCurses GUI started on {platform.system()}", 1)
            self.add_output_line(f"Timeouts: Scan={self.mgr.scan_timeout}s, Response={self.mgr.response_timeout}s", 4)
            self.add_output_line("Visual feedback enabled - watch for spinners and progress bars", 4)
            self.add_output_line("Type 'debug' to toggle debug mode, 'help' for commands", 4)
            
            last_command_time = 0
            command_cooldown = 0.5
            
            while self.running:
                try:
                    self.draw_screen()
                    
                    self.stdscr.timeout(25 if not self.waiting_for_response else 50)
                    try:
                        key = self.stdscr.getch()
                    except:
                        key = -1
                        
                    current_time = time.time()
                    
                    if key == -1:
                        continue
                    elif key == curses.KEY_UP:
                        if self.history and self.history_pos > 0:
                            self.history_pos -= 1
                            self.current_command = self.history[self.history_pos]
                            self.cursor_pos = len(self.current_command)
                    elif key == curses.KEY_DOWN:
                        if self.history and self.history_pos < len(self.history) - 1:
                            self.history_pos += 1
                            self.current_command = self.history[self.history_pos]
                            self.cursor_pos = len(self.current_command)
                        elif self.history_pos == len(self.history) - 1:
                            self.history_pos = len(self.history)
                            self.current_command = ""
                            self.cursor_pos = 0
                    elif key == curses.KEY_LEFT:
                        if self.cursor_pos > 0:
                            self.cursor_pos -= 1
                    elif key == curses.KEY_RIGHT:
                        if self.cursor_pos < len(self.current_command):
                            self.cursor_pos += 1
                    elif key == ord('\t'):
                        if not self.waiting_for_response:
                            self.handle_tab_completion()
                    elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                        if (not self.waiting_for_response and 
                            self.current_command.strip() and 
                            current_time - last_command_time > command_cooldown):
                            
                            if not self.history or self.history[-1] != self.current_command:
                                self.history.append(self.current_command)
                            self.history_pos = len(self.history)
                            
                            last_command_time = current_time
                            self.execute_command(self.current_command)
                            
                            self.current_command = ""
                            self.cursor_pos = 0
                    elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                        if not self.waiting_for_response and self.cursor_pos > 0:
                            self.current_command = self.current_command[:self.cursor_pos-1] + self.current_command[self.cursor_pos:]
                            self.cursor_pos -= 1
                    elif key == 3:  # CTRL+C
                        if self.waiting_for_response:
                            self.cancel_operation()
                            continue
                        else:
                            self.running = False
                    elif 32 <= key <= 126:
                        if not self.waiting_for_response:
                            char = chr(key)
                            self.current_command = self.current_command[:self.cursor_pos] + char + self.current_command[self.cursor_pos:]
                            self.cursor_pos += 1
                            
                except Exception as e:
                    try:
                        self.add_output_line(f"GUI Error: {str(e)[:50]}", 3)
                    except:
                        pass
                        
        except KeyboardInterrupt:
            self.running = False
        finally:
            self.stop_wait_feedback()
            self.stop_output_capture()
            self.cleanup_curses()
            
def setup_readline():
    if not HAS_READLINE:
        return
    
    def complete_commands(text, state):
        base_commands = ["exit", "scan", "device", "deviceinfo", "help", "setmac", "loadconfig", "saveconfig", "debug", "production_mode"]
        at_commands = [f"at+{cmd}" for cmd in PRODUCTION_SET_COMMANDS + PRODUCTION_GET_COMMANDS]
        at_get_commands = [f"at+{cmd}?" for cmd in PRODUCTION_GET_COMMANDS]
        
        all_commands = base_commands + at_commands + at_get_commands
        
        matches = [cmd for cmd in all_commands if cmd.lower().startswith(text.lower())]
        
        if state < len(matches):
            return matches[state]
        else:
            return None
    
    readline.set_completer(complete_commands)
    
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
    readline.set_completer_delims(' \t\n')

def select_device(devices):
    if len(devices) == 1:
        return devices[0]
    elif len(devices) > 1:
        print("Select a device to send commands to:")
        for idx, device in enumerate(devices):
            device_mac = ':'.join(f'{b:02x}' for b in device)
            print(f"{idx + 1}. {device_mac}")
        
        while True:
            try:
                choice = int(input("Enter the device number: ")) - 1
                if 0 <= choice < len(devices):
                    return devices[choice]
                else:
                    print(f"Please enter a number between 1 and {len(devices)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(1)
    else:
        print("No devices found.")
        sys.exit(1)

def parse_mac_address(mac_str):
    try:
        return bytes(int(x, 16) for x in mac_str.split(':'))
    except ValueError:
        print("Invalid MAC address format")
        sys.exit(1)

def parse_at_response(response_list):
    if not response_list:
        return ""
    
    if isinstance(response_list, list):
        full_response = ''.join(response_list)
    else:
        full_response = response_list
    
    lines = full_response.strip().split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if line and line != "OK" and "valid cmds:" not in line:
            if line.startswith('+') and ':' in line:
                cmd_part, value_part = line.split(':', 1)
                value = value_part.strip()
                if value:
                    clean_lines.append(value)
    
    combined = ' '.join(clean_lines)
    
    if len(combined) > 175:
        return '\n'.join(clean_lines)
    else:
        return combined if combined else full_response.strip()

def send_device_info_commands(mgr):
    info_commands = ["at+ssid?", "at+mode?", "at+keymgmt?", "at+psk?", "at+bss_bw?", "at+chan_list?"]
    
    print("Getting device information...")
    
    for cmd in info_commands:
        print(f"Querying: {cmd}")
        
        mgr.start_packet_capture()
        mgr.netat_send(cmd)
        
        devices, responses = mgr.wait_for_responses(timeout_seconds=mgr.response_timeout, early_exit_for_commands=True)
        mgr.stop_packet_capture()
        
        if responses:
            combined_response = parse_at_response(responses)
            param_name = cmd.replace("at+", "").replace("?", "").upper()
            print(f"{param_name}: {combined_response}")
            
            if mgr.log_responses:
                device_mac = ':'.join(f'{b:02x}' for b in mgr.dest)
                mgr.log_response(cmd, combined_response, device_mac)
        else:
            param_name = cmd.replace("at+", "").replace("?", "").upper()
            print(f"{param_name}: No response")
        
        time.sleep(0.1)

def load_config_file(mgr, filename):
    try:
        print(f"Loading configuration from: {filename}")
        
        if not os.path.exists(filename):
            print(f"Config file not found: {filename}")
            return
        
        commands_applied = 0
        commands_failed = 0
        
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        print(f"Found {len(lines)} lines in config file")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            if '=' in line:
                param, value = line.split('=', 1)
                param = param.strip()
                value = value.strip()
                
                at_command = f"at+{param}={value}"
                
                print(f"Line {line_num}: {at_command}")
                
                mgr.start_packet_capture()
                mgr.netat_send(at_command)
                
                devices, responses = mgr.wait_for_responses(timeout_seconds=mgr.response_timeout, early_exit_for_commands=True)
                mgr.stop_packet_capture()
                
                if responses:
                    combined_response = parse_at_response(responses)
                    if "OK" in combined_response or combined_response.strip():
                        print(f"{param} set successfully")
                        commands_applied += 1
                    else:
                        print(f"{param} failed: {combined_response}")
                        commands_failed += 1
                else:
                    print(f"{param} failed: No response")
                    commands_failed += 1
                
                time.sleep(0.2)
            else:
                print(f"Line {line_num}: Invalid format (expected param=value)")
                commands_failed += 1
        
        total_commands = commands_applied + commands_failed
        print(f"Configuration complete: {commands_applied}/{total_commands} applied successfully")
        
    except Exception as e:
        print(f"Error loading config file: {e}")

def save_config_file(mgr, filename):
    try:
        print(f"Saving configuration to: {filename}")
        
        config_commands = [
            ("ssid", "at+ssid?"),
            ("mode", "at+mode?"), 
            ("keymgmt", "at+keymgmt?"),
            ("psk", "at+psk?"),
            ("bss_bw", "at+bss_bw?"),
            ("chan_list", "at+chan_list?"),
        ]
        
        config_data = {}
        successful_queries = 0
        
        print(f"Querying {len(config_commands)} parameters...")
        
        for param_name, at_cmd in config_commands:
            mgr.start_packet_capture()
            mgr.netat_send(at_cmd)
            
            devices, responses = mgr.wait_for_responses(timeout_seconds=mgr.response_timeout, early_exit_for_commands=True)
            mgr.stop_packet_capture()
            
            if responses:
                combined_response = parse_at_response(responses)
                if combined_response and combined_response != "ERROR":
                    config_data[param_name] = combined_response
                    successful_queries += 1
                    print(f"Got {param_name}: {combined_response[:30]}{'...' if len(combined_response) > 30 else ''}")
                else:
                    print(f"{param_name}: Invalid response")
            else:
                print(f"{param_name}: No response")
            
            time.sleep(0.1)
        
        if config_data:
            with open(filename, 'w') as f:
                f.write(f"# Device Configuration - Saved {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Device MAC: {':'.join(f'{b:02x}' for b in mgr.dest)}\n")
                f.write(f"# Format: parameter=value (without 'at+' prefix)\n")
                f.write(f"# Use 'loadconfig {filename}' to restore these settings\n\n")
                
                for param, value in config_data.items():
                    f.write(f"{param}={value}\n")
            
            print(f"Configuration saved: {successful_queries} parameters written to {filename}")
            print(f"Use 'loadconfig {filename}' to restore settings")
        else:
            print("No configuration data retrieved - cannot save file")
            
    except Exception as e:
        print(f"Error saving config file: {e}")

def print_help():
    print("\n" + "=" * 70)
    print(f"Taixin LibNetat Tool  ({platform.system().upper()})")
    print("=" * 70)
    print("\nBASIC COMMANDS:")
    print("  exit                    - Exit the program")
    print("  scan                    - Scan for devices")
    print("  device                  - Show current device MAC")
    print("  deviceinfo              - Get comprehensive device info")
    print("  setmac <mac>            - Set destination MAC address")
    print("  loadconfig <file>       - Load settings from config file")
    print("  saveconfig [file]       - Save current settings to file")
    print("  logging                 - Toggle response logging")
    print("  debug                   - Toggle debug mode (enables debug commands)")
    print("  production_mode         - Disable debug commands")
    print("  help                    - Show this help message")
    
    print("\nCONFIG FILE FORMAT:")
    print("  # Comments start with # or //")
    print("  ssid=MyNetwork")
    print("  psk=MyPassword")
    print("  mode=1")
    print("  keymgmt=WPA2-PSK")
    print("  channel=6")
    
    print("\nAT COMMANDS:")
    print("  at+<command>=<value>    - Set parameter")
    print("  at+<command>?           - Get parameter value")
    print("  at+<command>            - Execute command")
    
    print("\nCOMMON EXAMPLES:")
    print("  at+ssid?                - Get current SSID")
    print("  at+ssid=MyNetwork       - Set SSID")
    print("  at+rssi?                - Get signal strength")
    print("  at+fwinfo?              - Get firmware info")
    print("  deviceinfo              - Get all device settings")
    print("  saveconfig backup.txt   - Save settings to file")
    print("  loadconfig backup.txt   - Restore settings from file")
    print("  logging                 - Toggle response logging")
    print("  debug                   - Enable debug commands")
    
    print("=" * 70 + "\n")

def main(ifname, command=None, dest_mac=None, debug=False, scan_timeout=8, response_timeout=5, enhanced_ui=False, log_responses=False, log_file="responses.log"):
    if not HAS_SCAPY:
        print("ERROR: Scapy is required for this version")
        print("Install with: pip install scapy")
        sys.exit(1)
    
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        filename="netat_scapy.log",
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Starting Working Scapy NetatMgr on {platform.system()}")

    try:
        mgr = ScapyNetAtMgr(ifname, debug=debug, scan_timeout=scan_timeout, response_timeout=response_timeout, log_responses=log_responses, log_file=log_file)
    except Exception as e:
        print(f"Failed to initialize network manager: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    if command == "scan":
        print("Scanning for devices using Scapy...")
        print(f"Interface: {mgr.ifname} ({mgr.interface_ip})")
        print(f"Broadcast to: {mgr.broadcast_ip}")
        print(f"Scan timeout: {scan_timeout}s")
        
        mgr.start_packet_capture()
        mgr.netat_scan()
        
        print("Waiting for responses...")
        devices, _ = mgr.wait_for_responses(timeout_seconds=scan_timeout, selected_device_only=False)
        mgr.stop_packet_capture()
        
        if devices:
            print(f"\nFound {len(devices)} device(s):")
            for device in devices:
                device_mac = ':'.join(f'{b:02x}' for b in device)
                print(f"  {device_mac}")
                logging.info(f"Found device: {device_mac}")
        else:
            print("\nNo devices found.")
        return

    if dest_mac:
        mgr.dest = parse_mac_address(dest_mac)
        logging.info(f"Destination MAC address set to: {':'.join(f'{b:02x}' for b in mgr.dest)}")
    else:
        print("Scanning for devices to connect to...")
        print(f"Scan timeout: {scan_timeout}s")
        mgr.start_packet_capture()
        mgr.netat_scan()
        devices, _ = mgr.wait_for_responses(timeout_seconds=scan_timeout, selected_device_only=False)
        mgr.stop_packet_capture()

        if devices:
            mgr.dest = select_device(devices)
            logging.info(f"Selected device: {':'.join(f'{b:02x}' for b in mgr.dest)}")
        else:
            print("No devices found. Please specify MAC address with --dest_mac")
            sys.exit(1)

    if command and command != "scan":
        print(f"Sending command: {command}")
        print(f"Response timeout: {response_timeout}s")
        mgr.start_packet_capture()
        mgr.netat_send(command)
        devices, responses = mgr.wait_for_responses(timeout_seconds=response_timeout, early_exit_for_commands=True, selected_device_only=True)
        mgr.stop_packet_capture()
        
        if responses:
            combined_response = parse_at_response(responses)
            print(f"Response: {combined_response}")
            logging.info(f"Received response: {' '.join(responses)}")
        else:
            print("No response received")
            logging.warning("No response from device")
    elif command == "deviceinfo":
        send_device_info_commands(mgr)
    elif command and command.startswith("loadconfig"):
        try:
            parts = command.split(None, 1)
            if len(parts) > 1:
                filename = parts[1]
                load_config_file(mgr, filename)
            else:
                print("Usage: --command 'loadconfig <filename>'")
        except Exception as e:
            print(f"Error loading config: {e}")
    elif command and command.startswith("saveconfig"):
        try:
            parts = command.split(None, 1)
            filename = parts[1] if len(parts) > 1 else "device_config.txt"
            save_config_file(mgr, filename)
        except Exception as e:
            print(f"Error saving config: {e}")
    else:
        if enhanced_ui and HAS_CURSES:
            try:
                interface = CursesInterface(mgr)
                interface.run()
            except ImportError:
                print("Curses not available, falling back to traditional mode")
                enhanced_ui = False
        
        if not enhanced_ui:
            setup_readline()
            
            print("\n" + "="*70)
            print(f"Taixin LibNetat Tool - CLI Mode")
            print("="*70)
            print(f"Device: {':'.join(f'{b:02x}' for b in mgr.dest)}")
            print(f"Interface: {mgr.ifname} ({mgr.interface_ip})")
            print(f"Timeouts: Scan={scan_timeout}s, Response={response_timeout}s")
            print("Tab completion enabled - try typing 'at+' and press Tab")
            print("Type 'help' for commands, 'debug' to toggle debug mode, or 'exit' to quit")
            print("Enhanced commands: deviceinfo, loadconfig, saveconfig, debug, logging")
            if mgr.log_responses:
                print(f"Response logging: ENABLED (file: {mgr.log_file})")
            else:
                print("Response logging: DISABLED (use 'logging' to enable)")
            print("="*70)
            
            while True:
                try:
                    input_cmd = input("\nnetat> ").strip()
                    if input_cmd.lower() == "exit":
                        break
                    elif input_cmd.lower() == "scan":
                        print("Scanning for devices...")
                        mgr.start_packet_capture()
                        mgr.netat_scan()
                        devices, _ = mgr.wait_for_responses(timeout_seconds=scan_timeout, selected_device_only=False)
                        mgr.stop_packet_capture()
                        
                        if devices:
                            print(f"\nFound {len(devices)} device(s):")
                            for device in devices:
                                device_mac = ':'.join(f'{b:02x}' for b in device)
                                print(f"  {device_mac}")
                            if len(devices) > 1:
                                mgr.dest = select_device(devices)
                            else:
                                mgr.dest = devices[0]
                                device_mac = ':'.join(f'{b:02x}' for b in devices[0])
                                print(f"Selected: {device_mac}")
                            
                            if mgr.log_responses:
                                new_filename = mgr.update_log_filename_for_device()
                                print(f"Log file updated: {new_filename}")
                        else:
                            print("No devices found.")
                    elif input_cmd.lower() == "device":
                        device_mac = ':'.join(f'{b:02x}' for b in mgr.dest)
                        print(f"Current device: {device_mac}")
                        print(f"Interface: {mgr.ifname} ({mgr.interface_ip})")
                    elif input_cmd.lower() == "deviceinfo":
                        send_device_info_commands(mgr)
                    elif input_cmd.lower() == "debug":
                        mgr.debug_mode = not mgr.debug_mode
                        mode_text = "enabled" if mgr.debug_mode else "disabled"
                        print(f"Debug mode {mode_text}")
                        commands_count = len(SET_COMMANDS) + len(GET_COMMANDS) if mgr.debug_mode else len(PRODUCTION_SET_COMMANDS) + len(PRODUCTION_GET_COMMANDS)
                        print(f"Available AT commands: {commands_count}")
                    elif input_cmd.lower() == "logging":
                        status = mgr.toggle_response_logging()
                        status_text = "enabled" if status else "disabled"
                        log_file = mgr.log_file if status else "N/A"
                        print(f"Response logging {status_text} (file: {log_file})")
                    elif input_cmd.lower() == "production_mode":
                        mgr.debug_mode = False
                        print("Production mode enabled (debug commands disabled)")
                    elif input_cmd.lower().startswith("setmac"):
                        try:
                            _, mac_str = input_cmd.split()
                            mgr.dest = parse_mac_address(mac_str)
                            device_mac = ':'.join(f'{b:02x}' for b in mgr.dest)
                            print(f"Device set to: {device_mac}")
                            
                            if mgr.log_responses:
                                new_filename = mgr.update_log_filename_for_device()
                                print(f"Log file updated: {new_filename}")
                        except:
                            print("Usage: setmac XX:XX:XX:XX:XX:XX")
                    elif input_cmd.lower().startswith("loadconfig"):
                        try:
                            parts = input_cmd.split(None, 1)
                            if len(parts) > 1:
                                filename = parts[1]
                                load_config_file(mgr, filename)
                            else:
                                print("Usage: loadconfig <filename>")
                        except Exception as e:
                            print(f"Error loading config: {e}")
                    elif input_cmd.lower().startswith("saveconfig"):
                        try:
                            parts = input_cmd.split(None, 1)
                            filename = parts[1] if len(parts) > 1 else "device_config.txt"
                            save_config_file(mgr, filename)
                        except Exception as e:
                            print(f"Error saving config: {e}")
                    elif input_cmd.lower() == "help":
                        print_help()
                    elif input_cmd.lower().startswith("at"):
                        print(f"Sending: {input_cmd}")
                        mgr.start_packet_capture()
                        mgr.netat_send(input_cmd)
                        devices, responses = mgr.wait_for_responses(timeout_seconds=response_timeout, early_exit_for_commands=True, selected_device_only=True)
                        mgr.stop_packet_capture()
                        
                        if responses:
                            combined_response = parse_at_response(responses)
                            print(f"Response: {combined_response}")
                            
                            if mgr.log_responses:
                                device_mac = ':'.join(f'{b:02x}' for b in mgr.dest)
                                mgr.log_response(input_cmd, combined_response, device_mac)
                        else:
                            print("No response received")
                    else:
                        if input_cmd.strip():
                            print(f"Unknown command: {input_cmd}")
                            print("Type 'help' for available commands")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except EOFError:
                    print("\nExiting...")
                    break

if __name__ == "__main__":
    if not HAS_SCAPY:
        print("ERROR: Scapy is required for this tool")
        print("Install with: pip install scapy")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Taixin Netat Tool - Working Scapy Edition")
    
    available_interfaces = get_network_interfaces()
    interface_help = f"Network interface to use. Available: {', '.join(available_interfaces[:3])}"
    if len(available_interfaces) > 3:
        interface_help += "..."
    interface_help += " Use 'auto' for automatic selection."
    
    parser.add_argument("interface", nargs='?', default='auto', help=interface_help)
    parser.add_argument("--command", help="Command to send (e.g., 'scan', 'at+fwinfo?', 'deviceinfo', 'saveconfig backup.txt', 'loadconfig backup.txt')")
    parser.add_argument("--dest_mac", help="Destination MAC address")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--scan-timeout", type=int, default=8, help="Scan timeout in seconds (default: 8)")
    parser.add_argument("--response-timeout", type=int, default=5, help="Response timeout in seconds (default: 5)")
    parser.add_argument("--enhanced", action="store_true", help="Use enhanced curses UI (if available)")
    parser.add_argument("--log-responses", action="store_true", help="Enable response logging")
    parser.add_argument("--log-file", default="responses.log", help="Log file for responses (default: responses.log)")
    parser.add_argument("--list-interfaces", action="store_true", help="List available network interfaces")
    parser.add_argument("--test-packet", action="store_true", help="Send test packet")
    
    args = parser.parse_args()
    
    if args.list_interfaces:
        interfaces = get_network_interfaces()
        print(f"\nAvailable network interfaces (Scapy detected):")
        for i, interface in enumerate(interfaces, 1):
            ip, mac = get_interface_info(interface)
            ip_display = ip if ip and ip != "0.0.0.0" else "No IP"
            mac_display = mac if mac else "Unknown MAC"
            print(f"  {i}. {interface:<12} - IP: {ip_display}, MAC: {mac_display}")
        print(f"\nPlatform: {platform.system()}")
        print(f"Recommended: {interfaces[0] if interfaces else 'None found'}")
        sys.exit(0)

    if args.test_packet:
        print(f"Testing packet transmission with Scapy on {args.interface}...")
        try:
            mgr = ScapyNetAtMgr(args.interface, debug=True)
            
            print("Starting packet capture...")
            mgr.start_packet_capture()
            
            test_data = b"SCAPY_TEST_" + str(int(time.time())).encode()
            print("Sending test packet...")
            mgr.send_packet(test_data)
            
            print("Waiting for packet capture...")
            time.sleep(1)
            mgr.stop_packet_capture()
            
            print("✓ Test packet sent successfully via Scapy")
            captured_count = len(mgr.captured_packets)
            if captured_count > 0:
                print(f"✓ Captured {captured_count} packets during test")
            else:
                print("! No packets captured (this may be normal depending on network setup)")
            
            print("\nTo verify packet transmission:")
            print(f"1. Run: sudo tcpdump -i {args.interface} udp port {NETAT_PORT}")
            print("2. Check Wireshark with filter: udp.port == 56789")
            print("3. Try running with sudo if needed")
            
        except Exception as e:
            print(f"✗ Test packet failed: {e}")
            if "Operation not permitted" in str(e) or "Permission denied" in str(e):
                print("Try running with sudo: sudo python3 fixed_netat_tool.py --test-packet")
            if args.debug:
                import traceback
                traceback.print_exc()
        sys.exit(0)

    print(f"Taixin LibNetat Tool - ({platform.system()})")
    print("=" * 55)
    print("Updates at https://github.com/aliosa27/taixin_tools")
    print("aliosa27@aliosa27.me")
    if args.debug:
        print("Debug mode enabled")
    print()

    try:
        main(
            ifname=args.interface,
            command=args.command,
            dest_mac=args.dest_mac,
            debug=args.debug,
            scan_timeout=args.scan_timeout,
            response_timeout=args.response_timeout,
            enhanced_ui=args.enhanced,
            log_responses=args.log_responses,
            log_file=args.log_file
        )
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        logging.error(f"Main error: {e}")
        sys.exit(1)
