import os
import sys
import socket
import struct
import fcntl

# Constants and Macros
MACSTR = "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}"
IPSTR = "{}.{}.{}.{}.{}"
HGIC = "hgics"
blenc_mode = 0

# Helper functions
def MAC2STR(mac):
    return MACSTR.format(*mac)

def STR_EQ(s1, s2):
    return s1 == s2

def MAC_EQ(a1, a2):
    return s1 == s2

def MAX(a, b):
    return max(a, b)

def hgics_dump_hex(prefix, data, newline):
    if data:
        output = []
        if prefix:
            output.append(prefix)
        for i, byte in enumerate(data):
            if newline and i > 0:
                if (i & 0x7) == 0:
                    output.append("   ")
                if (i & 0xf) == 0:
                    output.append("\n")
            output.append("{:02x} ".format(byte))
        output.append("\n")
        print("".join(output))

def put_unaligned_le16(val, p):
    p[0] = val & 0xff
    p[1] = (val >> 8) & 0xff

def get_unaligned_le16(p):
    return p[0] | (p[1] << 8)

def hgic_str2mac(mac_str):
    mac = [0] * 6
    if mac_str:
        parts = mac_str.split(':')
        if len(parts) == 6:
            for i, part in enumerate(parts):
                mac[i] = int(part, 16)
            return bytes(mac)
    return None

def hgic_get_if_mac(ifname):
    mac = [0] * 6
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ifr = array.array('B', bytes(ifname[:15], 'utf-8') + b'\x00' * (32 - len(ifname)))
    try:
        fcntl.ioctl(s.fileno(), 0x8927, ifr)
        mac = ifr[18:24]
    except IOError as e:
        print(f"Socket error: {e}")
    finally:
        s.close()
    return mac

def hgic_iwpriv_write(buff):
    file_path = f"/proc/{HGIC}/iwpriv"
    try:
        with open(file_path, 'wb') as fd:
            fd.write(buff)
    except IOError as e:
        print(f"Open {file_path} fail: {e}")
        return -1
    return len(buff)

def hgic_proc_read_bytes(buff_len):
    file_path = f"/proc/{HGIC}/iwpriv"
    try:
        with open(file_path, 'rb') as fd:
            return fd.read(buff_len)
    except IOError:
        return b''

def hgic_iwpriv_do(cmd, in_data=None, in_len=0, out_len=4096):
    ret = len(cmd)
    len_total = ret + MAX(in_len, out_len)
    buff = bytearray(len_total)

    if in_data and in_len:
        cmd_bytes = cmd.encode() + in_data[:in_len]
    else:
        cmd_bytes = cmd.encode()

    ret = hgic_iwpriv_write(cmd_bytes)
    if ret > 0:
        response = hgic_proc_read_bytes(len_total)
        if response:
            ret = int.from_bytes(response[:4], 'little')
            if ret > 0 and out_len > 0:
                return ret, response[4:4 + ret]
            return ret, response
        else:
            print("No response received from iwpriv")
    else:
        print(f"Failed to write command '{cmd}'")

    return ret, b''

# Function translations
def hgic_hw_state(state):
    states = {
        0: "Disconnect",
        1: "DISABLED",
        2: "INACTIVE",
        3: "SCANNING",
        4: "AUTHENTICATING",
        5: "ASSOCIATING",
        6: "ASSOCIATED",
        7: "4WAY_HANDSHAKE",
        8: "GROUP_HANDSHAKE",
        9: "CONNECTED"
    }
    return states.get(state, "Unknown")

def check_hgic_exists():
    global HGIC
    if os.path.exists("/proc/hgicf/iwpriv"):
        HGIC = "hgicf"
    elif os.path.exists("/proc/hgics/iwpriv"):
        HGIC = "hgics"
    else:
        print("Neither /proc/hgicf/iwpriv nor /proc/hgics/iwpriv exists")
        return False
    return True

# Main function
def main(argv):
    if len(argv) < 2:
        return -1

    if not check_hgic_exists():
        return -1

    try:
        buff = bytearray(4096)
    except MemoryError:
        print("no mem")
        return -1

    cmd = ' '.join(argv[1:])
    
    buff[:] = b'\x00' * 4096
    ret, buff = hgic_iwpriv_do(cmd, out_len=4096)
    if ret > 0:
        response = buff.decode(errors='ignore').strip()
        print(f"RESP:{ret}\n{response}")
    else:
        print("No response received")

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
