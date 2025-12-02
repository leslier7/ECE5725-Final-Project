#ifndef DONGLEPARSE_H
#define DONGLEPARSE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float x;
    float y;
    float z;
} Sensor;

struct dp_packet {
    uint8_t pipe;
    uint8_t button;
    uint16_t seq;
    Sensor accel;
    Sensor gyro;
};



/* Open the dongle serial device. Returns a file descriptor or -1 on error. */
int dp_open(const char *path, int baud);

/* Close device opened by dp_open. */
void dp_close(int fd);

/* Blocking read for next valid packet.
   Returns:
     1  - packet successfully read and filled into pkt
     0  - EOF (peer closed)
    -1  - read or io error
*/
int dp_read_packet(int fd, struct dp_packet *pkt);

#ifdef __cplusplus
}
#endif

#endif