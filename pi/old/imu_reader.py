# imu_reader.py
import serial
from dongleparse import DongleReader, IMU
from dataclasses import dataclass

@dataclass
class Angle:
    x: float
    y: float
    z: float


class IMUReader:
    """Unified IMU Reader for both dongle mode and serial text mode."""

    def __init__(self, mode: str, port: str, baud: int):
        self.mode = mode
        self.port = port
        self.baud = baud

        if mode == "dongle":
            self.reader = DongleReader(port=port, baud=baud)
            self.seq = 0
        elif mode == "serial":
            self.ser = serial.Serial(port, baud)
            self.seq = 0
        else:
            raise ValueError("mode must be 'dongle' or 'serial'")

    def parse_text_line(self, line: str):
        parts = line.split()
        if len(parts) < 6:
            return None

        if "accel" in line:
            ax = float(parts[1].split(":")[1])
            ay = float(parts[3].split(":")[1])
            az = float(parts[5].split(":")[1])
            return ("accel", Angle(ax, ay, az))

        if "gyro" in line:
            gx = float(parts[1].split(":")[1])
            gy = float(parts[3].split(":")[1])
            gz = float(parts[5].split(":")[1])
            return ("gyro", Angle(gx, gy, gz))

        return None

    def read_frame(self):
        """return(pipe, button, imu, seq) in both dongle and serial mode"""

        
        if self.mode == "dongle":
            pipe, button, imu, seq = self.reader.read_frame()
            return pipe, button, imu, seq

        elif self.mode == "serial":
            accel = gyro = None

            while True:
                raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
                print("RAW:", raw)
                if not raw:
                    continue

                parsed = self.parse_text_line(raw)
                if not parsed:
                    continue

                typ, value = parsed
                if typ == "accel":
                    accel = value
                elif typ == "gyro":
                    gyro = value

                if accel and gyro:
                    imu = IMU(
                        accel=accel,
                        gyro=gyro
                    )
                    self.seq += 1
                    return 0, 0, imu, self.seq
    
