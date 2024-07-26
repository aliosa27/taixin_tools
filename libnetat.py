import socket
import struct
import random
import time

NETAT_BUFF_SIZE = 1024
NETAT_PORT = 56789

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

class NetatMgr:
    def __init__(self, ifname):
        self.sock = None
        self.dest = b'\xff\xff\xff\xff\xff\xff'
        self.cookie = self.random_bytes(6)
        self.recvbuf = bytearray(NETAT_BUFF_SIZE)
        self.init_socket(ifname)

    def init_socket(self, ifname):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, 25, ifname.encode())

        local_addr = ('', NETAT_PORT)
        self.sock.bind(local_addr)

    def random_bytes(self, length):
        return bytes([random.randint(0, 255) for _ in range(length)])

    def sock_send(self, data):
        dest = ('<broadcast>', NETAT_PORT)
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

    def netat_send(self, atcmd):
        len_cmd = len(atcmd)
        cmd = WnbNetatCmd(WNB_NETAT_CMD_AT_REQ, self.dest, self.cookie, atcmd.encode())
        self.sock_send(cmd.to_bytes())

    def netat_recv(self, timeout_ms):
        while True:
            data = self.sock_recv(timeout_ms)
            if data is None:
                break

            cmd = WnbNetatCmd.from_bytes(data)
            if cmd.dest == self.cookie:
                if cmd.cmd == WNB_NETAT_CMD_SCAN_RESP:
                    self.dest = cmd.src
                elif cmd.cmd == WNB_NETAT_CMD_AT_RESP:
                    return cmd.data.decode()
        return None

def main(ifname, command=None):
    mgr = NetatMgr(ifname)
    mgr.netat_scan()
    time.sleep(1)  # wait for the scan to complete
    mgr.netat_recv(1000)

    if command:
        mgr.netat_send(command)
        response = mgr.netat_recv(1000)
        print(response)
    else:
        while True:
            try:
                input_cmd = input("\n>: ")
                if input_cmd.lower().startswith("at"):
                    mgr.netat_send(input_cmd)
                    response = mgr.netat_recv(1000)
                    print(response)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: {} <interface> [command]".format(sys.argv[0]))
    else:
        ifname = sys.argv[1]
        command = sys.argv[2] if len(sys.argv) > 2 else None
        main(ifname, command)
