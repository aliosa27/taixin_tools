#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#include <string.h>
#include <poll.h>
#include <time.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <linux/if.h>
#include <linux/if_packet.h>
#include <linux/if_ether.h>

#define MAC2STR(a) a[0], a[1], a[2], a[3], a[4], a[5]
#define MACSTR     "%02x:%02x:%02x:%02x:%02x:%02x"

#define NETAT_BUFF_SIZE (4096)
#define NETAT_PORT      (56789)

enum WNB_NETAT_CMD {
    WNB_NETAT_CMD_SCAN_REQ = 1,
    WNB_NETAT_CMD_SCAN_RESP,
    WNB_NETAT_CMD_AT_REQ,
    WNB_NETAT_CMD_AT_RESP,
};

struct wnb_netat_cmd {
    char  cmd;
    char  len[2];
    char  dest[6];
    char  src[6];
    char  data[0];
};

struct netat_mgr {
    int sock;
    char dest[6];
    char cookie[6];
    char recvbuf[NETAT_BUFF_SIZE];
} libnetat;

static void random_bytes(char *buff, int len)
{
    int i = 0;
    srand(time(NULL));
    for (i = 0; i < len; i++) {
        buff[i] = (char)(rand() & 0xff);
    }
}

static int sock_send(int sock, char *data, int len)
{
    int addr_len = sizeof(struct sockaddr_in);
    struct sockaddr_in dest;

    memset(&dest, 0, sizeof(struct sockaddr_in));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = INADDR_BROADCAST;
    dest.sin_port = htons(NETAT_PORT);
    return sendto(sock, data, len, 0, (struct sockaddr *)&dest, addr_len);
}

static int sock_recv(int sock, struct sockaddr_in *dest, char *data, int len, int tmo)
{
    int ret = 0;
    fd_set rfd;
    struct timeval timeout;
    int addr_len = sizeof(struct sockaddr_in);

    FD_ZERO(&rfd);
    FD_SET(sock, &rfd);
    timeout.tv_sec  = 0;
    timeout.tv_usec = tmo * 1000;

    ret = select(sock + 1, &rfd, NULL, NULL, &timeout);
    if (ret > 0 && FD_ISSET(sock, &rfd)) {
        ret = recvfrom(sock, data, len, 0, (struct sockaddr *)dest, &addr_len);
    }

    return ret;
}

static void netat_scan(void)
{
    struct wnb_netat_cmd scan;

    random_bytes(libnetat.cookie, 6);
    memset(&scan, 0, sizeof(scan));
    scan.cmd = WNB_NETAT_CMD_SCAN_REQ;
    memset(scan.dest, 0xff, 6);
    memcpy(scan.src, libnetat.cookie, 6);
    sock_send(libnetat.sock, (char *)&scan, sizeof(scan));
}

static void netat_send(char *atcmd)
{
    unsigned short len = strlen(atcmd);
    struct wnb_netat_cmd *cmd = (struct wnb_netat_cmd *)malloc(strlen(atcmd) + sizeof(struct wnb_netat_cmd));

    if (cmd) {
        random_bytes(libnetat.cookie, 6);
        len = htons(len);
        memset(cmd, 0, sizeof(struct wnb_netat_cmd));
        cmd->cmd = WNB_NETAT_CMD_AT_REQ;
        memcpy(cmd->len, &len, 2);
        memcpy(cmd->dest, libnetat.dest, 6);
        memcpy(cmd->src, libnetat.cookie, 6);
        memcpy(cmd->data, atcmd, strlen(atcmd));
        sock_send(libnetat.sock, (char *)cmd, strlen(atcmd) + sizeof(struct wnb_netat_cmd));
        free(cmd);
    }
}

static int netat_recv(char *buff, int len, int tmo)
{
    int ret;
    int off = 0;
    struct sockaddr_in from;
    struct wnb_netat_cmd *cmd;

    do {
        memset(libnetat.recvbuf, 0, NETAT_BUFF_SIZE);
        ret = sock_recv(libnetat.sock, &from, libnetat.recvbuf, NETAT_BUFF_SIZE, tmo);
        if (ret >= sizeof(struct wnb_netat_cmd)) {
            cmd = (struct wnb_netat_cmd *)libnetat.recvbuf;
            if (memcmp(cmd->dest, libnetat.cookie, 6) == 0) {
                switch (cmd->cmd) {
                    case WNB_NETAT_CMD_SCAN_RESP:
                        memcpy(libnetat.dest, cmd->src, 6);
                        break;
                    case WNB_NETAT_CMD_AT_RESP:
                        if (buff) {
                            strncpy(buff + off, cmd->data, ret - sizeof(struct wnb_netat_cmd));
                            off += (ret - sizeof(struct wnb_netat_cmd));
                        } else {
                            printf("%s\r\n", cmd->data);
                        }
                        break;
                    default:
                        break;
                }
            }
        }
    } while (ret > 0);
    if (buff) { buff[off] = 0; }
    return off;
}

int libnetat_init(char *ifname)
{
    int on = 1;
    struct sockaddr_in local_addr;
    struct ifreq req;

    memset(libnetat.dest, 0xff, 6);
    libnetat.sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (libnetat.sock < 0) {
        printf("create udp socket error:[%d:%s]\n", errno, strerror(errno));
        return -1;
    }

    memset(&local_addr, 0, sizeof(struct sockaddr_in));
    local_addr.sin_family = AF_INET;
    local_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    local_addr.sin_port = htons(NETAT_PORT);

    if (setsockopt(libnetat.sock, SOL_SOCKET, SO_BROADCAST, (const char *)&on, sizeof(on)) < 0) {
        close(libnetat.sock);
        libnetat.sock = 0;
        return -1;
    }

    strcpy(req.ifr_name, ifname);
    if (setsockopt(libnetat.sock, SOL_SOCKET, SO_BINDTODEVICE, (const char *)&req, sizeof(req)) < 0) {
        close(libnetat.sock);
        libnetat.sock = 0;
        return -1;
    }

    if (bind(libnetat.sock, (struct sockaddr *)&local_addr, sizeof(struct sockaddr_in)) < 0) {
        printf("udp bind error:[%d:%s]\n", errno, strerror(errno));
        close(libnetat.sock);
        return -1;
    }

    netat_scan();
    netat_recv(NULL, 0, 1);
    return 0;
}

int libnetat_send(char *atcmd, char *resp_buff, int buf_size)
{
    if (libnetat.sock == 0) {
        printf("libnetat is not inited!\r\n");
        return -1;
    }

    if (libnetat.dest[0] & 0x1) {
        netat_scan();
        netat_recv(NULL, 0, 100);
    }

    if (libnetat.dest[0] & 0x1) {
        printf("not detect device!\r\r");
        return -1;
    }

    netat_send(atcmd);
    return netat_recv(resp_buff, buf_size, 10);
}

void parse_mac_address(char *mac_str, char *mac) {
    int values[6];
    if (sscanf(mac_str, MACSTR, &values[0], &values[1], &values[2], &values[3], &values[4], &values[5]) == 6) {
        for (int i = 0; i < 6; i++) {
            mac[i] = (char)values[i];
        }
    } else {
        printf("Invalid MAC address format\n");
        exit(1);
    }
}

void handle_scan(int interactive) {
    netat_scan();
    char devices[128][6];
    int num_devices = 0;

    int ret;
    struct sockaddr_in from;
    struct wnb_netat_cmd *cmd;

    do {
        memset(libnetat.recvbuf, 0, NETAT_BUFF_SIZE);
        ret = sock_recv(libnetat.sock, &from, libnetat.recvbuf, NETAT_BUFF_SIZE, 1000);
        if (ret >= sizeof(struct wnb_netat_cmd)) {
            cmd = (struct wnb_netat_cmd *)libnetat.recvbuf;
            if (cmd->cmd == WNB_NETAT_CMD_SCAN_RESP) {
                if (num_devices < 128) {
                    memcpy(devices[num_devices++], cmd->src, 6);
                }
            }
        }
    } while (ret > 0);

    if (interactive) {
        if (num_devices == 1) {
            memcpy(libnetat.dest, devices, 6);
        } else if (num_devices > 1) {
            printf("Select a device to send commands to:\n");
            for (int i = 0; i < num_devices; i++) {
                printf("%d. " MACSTR "\n", i + 1, MAC2STR(devices[i]));
            }
            printf("Enter the device number: ");
            fflush(stdout);
            int choice;
            scanf("%d", &choice);
            if (choice >= 1 && choice <= num_devices) {
                memcpy(libnetat.dest, devices[choice - 1], 6);
            } else {
                printf("Invalid choice.\n");
                exit(1);
            }
        } else {
            printf("No devices found.\n");
            exit(1);
        }
    } else {
        // Non-interactive mode: print all detected devices
        for (int i = 0; i < num_devices; i++) {
            printf(MACSTR "\n", MAC2STR(devices[i]));
        }
    }
}

#if 1 //sample code
int main(int argc, char *argv[])
{
    char *ifname = NULL;
    char input[256];
    char response[1024];

    if (argc < 2) {
        printf("Usage: %s <interface> [command] [dest_mac]\n", argv[0]);
        return -1;
    }

    ifname = argv[1];

    if (libnetat_init(ifname)) {
        printf("libnetat init fail, interface: %s\n", ifname);
        return -1;
    }

    if (argc == 3) {
        // Non-interactive mode
        char *command = argv[2];
        if (strcmp(command, "scan") == 0) {
            handle_scan(0);
        } else {
            libnetat_send(command, response, sizeof(response));
            printf("%s", response);
        }
        return 0;
    } else if (argc == 4) {
        // Non-interactive mode with MAC address setting
        char *command = argv[2];
        char *mac_str = argv[3];
        parse_mac_address(mac_str, libnetat.dest);
        if (strcmp(command, "scan") == 0) {
            handle_scan(0);
        } else {
            libnetat_send(command, response, sizeof(response));
            printf("%s", response);
        }
        return 0;
    }

    // Interactive mode
    while (1) {
        memset(input, 0, sizeof(input));
        printf(">: ");
        fflush(stdout);
        fgets(input, sizeof(input), stdin);
        if (strlen(input) > 0) {
            input[strcspn(input, "\n")] = 0; // Remove newline character

            if (strcmp(input, "exit") == 0) {
                break;
            } else if (strcmp(input, "scan") == 0) {
                handle_scan(1);
            } else if (strcmp(input, "device") == 0) {
                printf("Current destination MAC address: " MACSTR "\n", MAC2STR(libnetat.dest));
            } else if (strncmp(input, "setmac", 6) == 0) {
                char mac_str[18];
                sscanf(input + 7, "%17s", mac_str);
                parse_mac_address(mac_str, libnetat.dest);
                printf("Destination MAC address set to " MACSTR "\n", MAC2STR(libnetat.dest));
            } else if (strncmp(input, "at", 2) == 0 || strncmp(input, "AT", 2) == 0) {
                libnetat_send(input, response, sizeof(response));
                printf("%s", response);
            }
        }
    }

    close(libnetat.sock);
    return 0;
}
#endif
