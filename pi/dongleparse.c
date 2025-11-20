#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
#include <math.h>

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

int main(int argc, char **argv) {
    const char *port = "/dev/ttyACM0";
    int baud = 115200;
    if (argc > 1) port = argv[1];
    if (argc > 2) baud = atoi(argv[2]);

    int fd = open_serial(port, baud);
    if (fd < 0) {
        fprintf(stderr, "Failed to open %s: %s\n", port, strerror(errno));
        return 1;
    }
    fprintf(stderr, "Listening on %s at %d baud...\n", port, baud);

    uint8_t sync[3] = {0};
    uint16_t last_seq = 0xFFFF;
    int have_last = 0;

    for (;;) {
        // find header
        while (1) {
            uint8_t b;
            ssize_t r = read_exact(fd, &b, 1);
            if (r <= 0) { fprintf(stderr, "Serial read error\n"); close(fd); return 1; }
            sync[0] = sync[1];
            sync[1] = sync[2];
            sync[2] = b;
            if (sync[0] == HEADER0 && sync[1] == HEADER1 && sync[2] == HEADER2) break;
        }

        // read payload + crc
        uint8_t buf[PAYLOAD_SIZE + CRC_SIZE];
        if (read_exact(fd, buf, sizeof(buf)) != (ssize_t)sizeof(buf)) {
            fprintf(stderr, "Short read\n");
            break;
        }

        uint16_t crc_recv = (uint16_t)buf[PAYLOAD_SIZE] | ((uint16_t)buf[PAYLOAD_SIZE + 1] << 8);
        uint16_t crc_calc = crc16_ccitt(buf, PAYLOAD_SIZE);
        if (crc_calc != crc_recv) {
            fprintf(stderr, "BAD CRC: calc=0x%04X recv=0x%04X, discarding\n", crc_calc, crc_recv);
            continue;
        }

        // parse payload (little-endian)
        uint8_t pipe = buf[0];
        uint8_t button = buf[1];
        uint16_t seq = (uint16_t)buf[2] | ((uint16_t)buf[3] << 8);

        float vals[6];
        for (int i = 0; i < 6; ++i) {
            uint8_t tmp[4];
            tmp[0] = buf[4 + i*4 + 0];
            tmp[1] = buf[4 + i*4 + 1];
            tmp[2] = buf[4 + i*4 + 2];
            tmp[3] = buf[4 + i*4 + 3];
            // assume host is little-endian and IEEE754 float
            float f;
            memcpy(&f, tmp, sizeof(f));
            vals[i] = f;
        }

        // sanity check
        int bad = 0;
        for (int i = 0; i < 6; ++i) {
            if (isnan(vals[i]) || isinf(vals[i]) || fabs(vals[i]) > 1e5f) { bad = 1; break; }
        }
        if (bad) {
            fprintf(stderr, "BAD VALUES despite CRC (pipe=%u, seq=%u)\n", pipe, seq);
            continue;
        }

        if (have_last) {
            uint16_t expected = (last_seq + 1) & 0xFFFF;
            if (seq != expected) {
                fprintf(stderr, "WARNING: seq jump %u -> %u\n", last_seq, seq);
            }
        }
        last_seq = seq; have_last = 1;

        if (button != 0) printf("Button pressed\n");
        printf("pipe=%u button=%u seq=%u accel=(% .3f, % .3f, % .3f) gyro=(% .3f, % .3f, % .3f)\n",
               pipe, button, seq,
               vals[0], vals[1], vals[2],
               vals[3], vals[4], vals[5]);
        fflush(stdout);
    }

    close(fd);
    return 0;
}