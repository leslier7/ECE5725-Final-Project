#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
#include <math.h>

#include "dongleparse.h"

#define HEADER0 0x77
#define HEADER1 0x55
#define HEADER2 0xAA

#define PAYLOAD_SIZE 28   // 1 + 1 + 2 + 6*4
#define CRC_SIZE 2

static uint16_t crc16_ccitt(const uint8_t *data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; ++b) {
            if (crc & 0x8000) crc = (crc << 1) ^ 0x1021;
            else crc = (crc << 1);
        }
    }
    return crc & 0xFFFF;
}

static ssize_t read_exact(int fd, void *buf, size_t n) {
    uint8_t *p = buf;
    size_t got = 0;
    while (got < n) {
        ssize_t r = read(fd, p + got, n - got);
        if (r < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (r == 0) return 0;
        got += r;
    }
    return (ssize_t)got;
}

static int open_serial(const char *path, int baud) {
    int fd = open(path, O_RDONLY | O_NOCTTY);
    if (fd < 0) return -1;
    struct termios tty;
    if (tcgetattr(fd, &tty) != 0) { close(fd); return -1; }
    cfmakeraw(&tty);
    speed_t sp;
    switch (baud) {
        case 115200: sp = B115200; break;
        case 57600: sp = B57600; break;
        case 38400: sp = B38400; break;
        case 19200: sp = B19200; break;
        case 9600:  sp = B9600;  break;
        default:    sp = B115200; break;
    }
    cfsetispeed(&tty, sp);
    cfsetospeed(&tty, sp);
    tty.c_cc[VMIN] = 1;
    tty.c_cc[VTIME] = 0;
    if (tcsetattr(fd, TCSANOW, &tty) != 0) { close(fd); return -1; }
    return fd;
}
// ...existing code...

int dp_open(const char *path, int baud) {
    return open_serial(path, baud);
}

void dp_close(int fd) {
    if (fd >= 0) close(fd);
}

/* Blocking read of next valid packet; removes main() and returns parsed data */
int dp_read_packet(int fd, struct dp_packet *pkt) {
    if (fd < 0 || pkt == NULL) return -1;

    uint8_t sync[3] = {0};
    for (;;) {
        // find header
        while (1) {
            uint8_t b;
            ssize_t r = read_exact(fd, &b, 1);
            if (r < 0) return -1;
            if (r == 0) return 0; // EOF
            sync[0] = sync[1];
            sync[1] = sync[2];
            sync[2] = b;
            if (sync[0] == HEADER0 && sync[1] == HEADER1 && sync[2] == HEADER2) break;
        }

        // read payload + crc
        uint8_t buf[PAYLOAD_SIZE + CRC_SIZE];
        ssize_t r = read_exact(fd, buf, sizeof(buf));
        if (r < 0) return -1;
        if (r == 0) return 0;
        if (r != (ssize_t)sizeof(buf)) return -1;

        uint16_t crc_recv = (uint16_t)buf[PAYLOAD_SIZE] | ((uint16_t)buf[PAYLOAD_SIZE + 1] << 8);
        uint16_t crc_calc = crc16_ccitt(buf, PAYLOAD_SIZE);
        if (crc_calc != crc_recv) {
            // discard and keep searching
            continue;
        }

        // parse payload (little-endian)
        pkt->pipe = buf[0];
        pkt->button = buf[1];
        pkt->seq = (uint16_t)buf[2] | ((uint16_t)buf[3] << 8);

        /* Read 6 floats: accel x,y,z then gyro x,y,z */
        float vals[6];
        for (int i = 0; i < 6; ++i) {
            memcpy(&vals[i], &buf[4 + i*4], sizeof(float));
        }

        // sanity check
        int bad = 0;
        for (int i = 0; i < 6; ++i) {
            if (isnan(vals[i]) || isinf(vals[i]) || fabs(vals[i]) > 1e5f) { bad = 1; break; }
        }
        if (bad) {
            continue;
        }

        // map into accel / gyro structs
        pkt->accel.x = vals[0];
        pkt->accel.y = vals[1];
        pkt->accel.z = vals[2];
        pkt->gyro.x  = vals[3];
        pkt->gyro.y  = vals[4];
        pkt->gyro.z  = vals[5];

        return 1; // success
    }
    // unreachable
    return -1;
}