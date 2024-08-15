import socket
import struct
import random
import time
import sys

NETAT_BUFF_SIZE = 4096  # Increase buffer size to handle longer commands
NETAT_PORT = 56789
NETLOG_PORT = 64320

WNB_NETAT_CMD_SCAN_REQ = 1
WNB_NETAT_CMD_SCAN_RESP = 2
WNB_NETAT_CMD_AT_REQ = 3
WNB_NETAT_CMD_AT_RESP = 4

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
        cmd, length, dest, src = struct.unpack('!B2s6s6s', data[:15])
        data = data[15:]
        return cls(cmd, dest, src, data)

class WnbModuleNetlog:
    def __init__(self, addr, cookie, ip, timestamp, port):
        self.addr = addr
        self.cookie = cookie
        self.ip = ip
        self.timestamp = timestamp
        self.port = port

    def to_bytes(self):
        return struct.pack('!6s6sIIBH', self.addr, self.cookie, self.ip, self.timestamp, 0, self.port)

    @classmethod
    def from_bytes(cls, data):
        addr, cookie, ip, timestamp, _, port = struct.unpack('!6s6sIIBH', data[:23])
        return cls(addr, cookie, ip, timestamp, port)

class NetatMgr:
    def __init__(self, ifname, port=NETAT_PORT):
        self.sock = None
        self.dest = b'\xff\xff\xff\xff\xff\xff'
        self.cookie = self.random_bytes(6)
        self.recvbuf = bytearray(NETAT_BUFF_SIZE)
        self.port = port
        self.init_socket(ifname)

    def init_socket(self, ifname):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, 25, ifname.encode())

        local_addr = ('', self.port)
        self.sock.bind(local_addr)

    def random_bytes(self, length):
        return bytes([random.randint(0, 255) for _ in range(length)])

    def sock_send(self, data):
        dest = ('<broadcast>', self.port)
        self.sock.sendto(data, dest)

    def sock_recv(self, timeout_ms):
        self.sock.settimeout(timeout_ms / 1000)
        try:
            data, addr = self.sock.recvfrom(NETAT_BUFF_SIZE)
            return data
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

    def netat_scan(self):
        self.cookie = self.random_bytes(6)
        scan_cmd = WnbNetatCmd(WNB_NETAT_CMD_SCAN_REQ, b'\xff\xff\xff\xff\xff\xff', self.cookie)
        self.sock_send(scan_cmd.to_bytes())

    def netlog_discover(self):
        self.cookie = self.random_bytes(6)
        ip = struct.unpack("!I", socket.inet_aton('255.255.255.255'))[0]
        timestamp = int(time.time())
        netlog_pkt = WnbModuleNetlog(b'\xff\xff\xff\xff\xff\xff', self.cookie, ip, timestamp, NETLOG_PORT)
        self.sock_send(netlog_pkt.to_bytes())

    def netat_send(self, atcmd):
        cmd = WnbNetatCmd(WNB_NETAT_CMD_AT_REQ, self.dest, self.cookie, atcmd.encode())
        self.sock_send(cmd.to_bytes())

    def netat_recv(self, timeout_ms, expecting_response=False):
        response = b""
        devices = []
        while True:
            data = self.sock_recv(timeout_ms)
            if data is None:
                break

            try:
                cmd = WnbNetatCmd.from_bytes(data)
                if cmd.dest == self.cookie:
                    if cmd.cmd == WNB_NETAT_CMD_SCAN_RESP:
                        devices.append(cmd.src)
                    elif cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                        response += cmd.data
                    if not expecting_response:
                        break
            except Exception as e:
                print(f"Error parsing data: {e}")

        if expecting_response:
            if response:
                return response.decode()
            else:
                print("No response from device or command not recognized.")
        else:
            return devices

    def netlog_recv(self, timeout_ms):
        devices = []
        while True:
            data = self.sock_recv(timeout_ms)
            if data is None:
                break
            try:
                netlog = WnbModuleNetlog.from_bytes(data)
                devices.append(netlog.addr)
            except Exception as e:
                print(f"Error parsing netlog response: {e}")

        return devices

def select_device(devices):
    if len(devices) == 1:
        return devices[0]
    elif len(devices) > 1:
        print("Select a device to send commands to:")
        for idx, device in enumerate(devices):
            print(f"{idx + 1}. {':'.join(f'{b:02x}' for b in device)}")
        choice = int(input("Enter the device number: ")) - 1
        return devices[choice]
    else:
        print("No devices found.")
        sys.exit(1)

def parse_mac_address(mac_str):
    try:
        return bytes(int(x, 16) for x in mac_str.split(':'))
    except ValueError:
        print("Invalid MAC address format")
        sys.exit(1)

def load_config_from_file(file_path):
    config_commands = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and '=' in line:
                    cmd, value = line.split('=', 1)
                    config_commands.append((cmd, value))
    except FileNotFoundError:
        print(f"Error: Config file {file_path} not found.")
        sys.exit(1)
    return config_commands

def netlog(ifname):
    mgr = NetatMgr(ifname, port=NETLOG_PORT)
    mgr.netlog_discover()
    time.sleep(1)  # wait for the scan to complete
    devices = mgr.netlog_recv(1000)
    if devices:
        selected_device = select_device(devices)
        mgr.dest = selected_device
        print(f"Selected device: {':'.join(f'{b:02x}' for b in mgr.dest)}")

        # Send 02 command
        mgr.netat_send("02")
        response = mgr.netat_recv(1000, expecting_response=True)
        if response:
            print(response)
        else:
            print("Invalid device")
    else:
        print("No devices found.")

def main(ifname, command=None, dest_mac=None, config_file=None):
    mgr = NetatMgr(ifname)

    if command == "netlog":
        netlog(ifname)
        return

    if command == "scan":
        mgr.netat_scan()
        time.sleep(2)  # Wait for responses
        devices = mgr.netat_recv(2000)
        if devices:
            for device in devices:
                print(':'.join(f'{b:02x}' for b in device))
        else:
            print("No devices found.")
        return

    if dest_mac:
        mgr.dest = parse_mac_address(dest_mac)
    else:
        while True:
            mgr.netat_scan()
            time.sleep(1)  # wait for the scan to complete
            devices = mgr.netat_recv(1000)

            if devices:
                mgr.dest = select_device(devices)
                break
            else:
                print("No devices found. Retrying...")
                time.sleep(1)

    if config_file:
        config_commands = load_config_from_file(config_file)
        for cmd, value in config_commands:
            full_command = f"AT+{cmd}={value}"
            print(f"Sending: {cmd} = {value}")  # Display parameter and value
            mgr.netat_send(full_command)
            response = mgr.netat_recv(1000, expecting_response=True)
            if response:
                print(response)
            else:
                print(f"Command {full_command} failed or no response received.")
        return

    if command:
        mgr.netat_send(command)
        response = mgr.netat_recv(1000, expecting_response=True)
        if response:
            print(response)
        else:
            print("Invalid device")
    else:
        while True:
            try:
                input_cmd = input("\n>: ").strip().lower()
                if input_cmd == "exit":
                    break
                elif input_cmd == "scan":
                    mgr.netat_scan()
                    time.sleep(1)
                    devices = mgr.netat_recv(1000)
                    if devices:
                        for device in devices:
                            print(':'.join(f'{b:02x}' for b in device))
                        mgr.dest = select_device(devices)
                    else:
                        print("No devices found.")
                elif input_cmd == "device":
                    print(f"Current destination MAC address: {':'.join(f'{b:02x}' for b in mgr.dest)}")
                elif input_cmd.startswith("at"):
                    mgr.netat_send(input_cmd)
                    response = mgr.netat_recv(1000, expecting_response=True)
                    if response:
                        print(response)
                    else:
                        print("Invalid device")
                elif input_cmd.startswith("setmac"):
                    _, mac_str = input_cmd.split()
                    mgr.dest = parse_mac_address(mac_str)
                    print(f"Destination MAC address set to {':'.join(f'{b:02x}' for b in mgr.dest)}")
                elif input_cmd.startswith("loadconfig"):
                    _, file_path = input_cmd.split()
                    config_commands = load_config_from_file(file_path)
                    for cmd, value in config_commands:
                        full_command = f"AT+{cmd}={value}"
                        print(f"Sending: {cmd} = {value}")  # Display parameter and value
                        mgr.netat_send(full_command)
                        response = mgr.netat_recv(1000, expecting_response=True)
                        if response:
                            print(response)
                        else:
                            print(f"Command {full_command} failed or no response received.")
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} <interface> [command] [dest_mac] [config_file]".format(sys.argv[0]))
    else:
        ifname = sys.argv[1]
        command = sys.argv[2] if len(sys.argv) > 2 else None
        dest_mac = sys.argv[3] if len(sys.argv) > 3 else None
        config_file = sys.argv[4] if len(sys.argv) > 4 else None
        main(ifname, command, dest_mac, config_file)
