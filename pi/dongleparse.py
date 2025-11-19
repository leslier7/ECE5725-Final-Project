import argparse
import serial
import struct
import math
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Sensor:
    x: float
    y: float
    z: float

@dataclass
class IMU:
    accel: Sensor
    gyro: Sensor

HEADER = b"\x77\x55\xAA"

# Layout: [ pipe:u8 | seq:u16 | 6 floats ]
PAYLOAD_FORMAT = "<B H ffffff"
PAYLOAD_SIZE   = struct.calcsize(PAYLOAD_FORMAT)   # 1 + 2 + 24 = 27
FRAME_SIZE     = len(HEADER) + PAYLOAD_SIZE + 2    # + CRC16 = 32

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

def read_exact(ser, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if not chunk:
            raise RuntimeError("Serial read returned no data")
        buf += chunk
    return buf

def find_header(ser) -> None:
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

def _parse_payload(payload: bytes) -> Tuple[int, IMU, int]:
    pipe, seq, ax, ay, az, gx, gy, gz = struct.unpack(PAYLOAD_FORMAT, payload)
    imu_data = IMU(Sensor(ax, ay, az), Sensor(gx, gy, gz))
    return pipe, imu_data, seq

class DongleReader:
    """High-level reader for the dongle protocol.

    Usage:
      dr = DongleReader(port="/dev/ttyACM0", baud=115200, hex_output=False)
      pipe, imu, seq = dr.read_frame()
      dr.close()
    """
    def __init__(self, port: Optional[str] = None, baud: int = 115200,
                 ser=None, hex_output: bool = False):
        if ser is not None:
            self.ser = ser
        else:
            if port is None:
                raise ValueError("Either ser or port must be provided")
            self.ser = serial.Serial(port, baud)
        self.hex = hex_output
        self.last_seq: Optional[int] = None

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def read_frame(self, skip_bad: bool = True) -> Tuple[int, IMU, int]:
        """Read and return (pipe, imu_data, seq).
        If skip_bad is True, bad CRC/values will be skipped and function will block until a good frame arrives.
        Otherwise a RuntimeError is raised on bad frames.
        """
        while True:
            # 1) sync to header
            find_header(self.ser)

            # 2) read payload + CRC
            rest = read_exact(self.ser, PAYLOAD_SIZE + 2)
            payload = rest[:PAYLOAD_SIZE]
            crc_bytes = rest[PAYLOAD_SIZE:]
            crc_recv = crc_bytes[0] | (crc_bytes[1] << 8)

            crc_calc = crc16_ccitt(payload)
            if crc_calc != crc_recv:
                if self.hex:
                    print("BAD CRC, discarding. HEX:", (HEADER + rest).hex(" "))
                if skip_bad:
                    continue
                raise RuntimeError("Bad CRC")

            if self.hex:
                print("HEX:", (HEADER + rest).hex(" "))

            pipe, imu_data, seq = _parse_payload(payload)

            # Optional: still keep a simple physical sanity check
            vals = (imu_data.accel.x, imu_data.accel.y, imu_data.accel.z,
                    imu_data.gyro.x, imu_data.gyro.y, imu_data.gyro.z)
            if any(math.isnan(v) or math.isinf(v) or abs(v) > 1e5 for v in vals):
                print(f"BAD VALUES despite CRC (pipe={pipe}, seq={seq}): {vals}")
                if skip_bad:
                    self.last_seq = seq
                    continue
                raise RuntimeError("Bad sensor values")

            if self.last_seq is not None and seq != (self.last_seq + 1) & 0xFFFF:
                print(f"WARNING: seq jump {self.last_seq} -> {seq}")
            self.last_seq = seq
            return pipe, imu_data, seq

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", default="/dev/ttyACM0", help="Serial port, e.g. /dev/ttyACM0")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--hex", action="store_true", help="Print raw frame hex")
    args = parser.parse_args()

    dr = DongleReader(port=args.port, baud=args.baud, hex_output=args.hex)
    print(f"Listening on {args.port} at {args.baud} baud...")
    try:
        while True:
            pipe, imu, seq = dr.read_frame()
            print(
                f"pipe={pipe} "
                f"accel=({imu.accel.x: .3f}, {imu.accel.y: .3f}, {imu.accel.z: .3f}) "
                f"gyro=({imu.gyro.x: .3f}, {imu.gyro.y: .3f}, {imu.gyro.z: .3f})"
            )
    finally:
        dr.close()