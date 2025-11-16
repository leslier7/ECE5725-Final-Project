import argparse
import serial
import struct
import math

parser = argparse.ArgumentParser()
parser.add_argument("port", help="Serial port, e.g. /dev/ttyACM0")
parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
parser.add_argument("--hex", action="store_true", help="Print raw frame hex")
args = parser.parse_args()

HEADER = b"\x77\x55\xAA"

# Layout: [ pipe:u8 | seq:u16 | 6 floats ]
PAYLOAD_FORMAT = "<B H ffffff"
PAYLOAD_SIZE   = struct.calcsize(PAYLOAD_FORMAT)   # 1 + 2 + 24 = 27
FRAME_SIZE     = len(HEADER) + PAYLOAD_SIZE + 2    # + CRC16 = 32

print("FRAME_SIZE =", FRAME_SIZE)

def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def read_exact(ser, n):
    buf = b""
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if not chunk:
            raise RuntimeError("Serial read returned no data")
        buf += chunk
    return buf

def find_header(ser):
    sync = b""
    while True:
        b1 = ser.read(1)
        if not b1:
            raise RuntimeError("Serial disconnected")
        sync += b1
        if len(sync) > len(HEADER):
            sync = sync[-len(HEADER):]
        if sync == HEADER:
            return

def main():
    ser = serial.Serial(args.port, args.baud)
    print(f"Listening on {args.port} at {args.baud} baud...")

    last_seq = None

    while True:
        # 1) sync to header
        find_header(ser)

        # 2) read payload + CRC
        rest = read_exact(ser, PAYLOAD_SIZE + 2)
        payload = rest[:PAYLOAD_SIZE]
        crc_bytes = rest[PAYLOAD_SIZE:]
        crc_recv = crc_bytes[0] | (crc_bytes[1] << 8)

        crc_calc = crc16_ccitt(payload)
        if crc_calc != crc_recv:
            if args.hex:
                print("BAD CRC, discarding. HEX:", (HEADER + rest).hex(" "))
            continue  # skip this frame

        if args.hex:
            print("HEX:", (HEADER + rest).hex(" "))

        pipe, seq, ax, ay, az, gx, gy, gz = struct.unpack(PAYLOAD_FORMAT, payload)

        # Optional: check for dropped frames
        if last_seq is not None and seq != (last_seq + 1) & 0xFFFF:
            print(f"WARNING: seq jump {last_seq} -> {seq}")
        last_seq = seq

        # Optional: still keep a simple physical sanity check
        vals = (ax, ay, az, gx, gy, gz)
        if any(math.isnan(v) or math.isinf(v) or abs(v) > 1e5 for v in vals):
            print(f"BAD VALUES despite CRC (pipe={pipe}, seq={seq}): {vals}")
            continue

        print(
            f"pipe={pipe} seq={seq} "
            f"accel=({ax: .3f}, {ay: .3f}, {az: .3f}) "
            f"gyro=({gx: .3f}, {gy: .3f}, {gz: .3f})"
        )

if __name__ == "__main__":
    main()
