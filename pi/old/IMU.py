import argparse
import serial
import time
import math
from dataclasses import dataclass
from dongleparse import DongleReader, Sensor, IMU
import os

@dataclass
class Angle:
    x: float
    y: float
    z: float

readMode = "dongle"

parser = argparse.ArgumentParser()
parser.add_argument("port", nargs="?", default="/dev/tty.usbmodem11101", help="Serial port, e.g. /dev/ttyACM0")
parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
parser.add_argument("--hex", action="store_true", help="Print raw frame hex")
args = parser.parse_args()

# init the serial port
# ser = serial.Serial('/dev/tty.usbmodem1101', 115200)

a_x = a_y = a_z = r_x = r_y = r_z = 0.0
angle_x = angle_y = angle_z = 0.0
calibration_time = 3.0
start_time = time.time()
rx_bias = ry_bias = rz_bias = 0.0


# Unified IMU Reader (Dongle mode or Serial-text mode)

class IMUReader:
    def __init__(self, mode, port, baud):
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

    def parse_text_line(self, line):
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

    # Unified read_frame() both modes produce same tuple
    def read_frame(self):
        if self.mode == "dongle":
            pipe, button, imu, seq = self.reader.read_frame()
            return pipe, button, imu, seq

        elif self.mode == "serial":
            # read text lines until we get accel + gyro
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
                    # simulate IMU object so main() stays the same
                    imu = IMU(
                        accel=accel,
                        gyro=gyro
                    )
                    self.seq += 1
                    return 0, 0, imu, self.seq



def get_angle_gyro(angle, gyro, last_time, gyro_in_radians: bool = True, wrap360: bool = True):
    
    now = time.time()
    dt = now - last_time
    last_time = now

    # TOOD convert to degrees
    # convert gyro to degrees/sec if it's in radians/sec
    if gyro_in_radians:
        conv = 180.0 / math.pi
    else:
        conv = 1.0

    angle.x += (gyro.x * conv) * dt
    angle.y += (gyro.y * conv) * dt
    angle.z += (gyro.z * conv) * dt

    if wrap360:
        angle.x %= 360.0
        angle.y %= 360.0
        angle.z %= 360.0

    return angle, last_time

def get_angle_accel(angle, accel, gravity, convert_to_degree: bool = True):
    # use arctangent to calculate the angle from the accelerometer
    angle.x = math.atan2(accel.x - gravity.x, math.sqrt((accel.y - gravity.y)**2 + (accel.z - gravity.z)**2))
    angle.y = math.atan2(accel.y - gravity.y, math.sqrt((accel.x - gravity.x)**2 + (accel.z - gravity.z)**2))
    angle.z = math.atan2(accel.z - gravity.z, math.sqrt((accel.x - gravity.x)**2 + (accel.y - gravity.y)**2))

    conv = 180.0 / math.pi
    if convert_to_degree:
        angle.x *= conv
        angle.y *= conv
        angle.z *= conv

    return angle

def calibrate_gyro(reader) -> list[Angle]: 
    # global rx_bias, ry_bias, rz_bias
    # global r_x, r_y, r_z
    gyroAngleSum = Angle(0, 0, 0)
    gyroBias = Angle(0, 0, 0)
    gravity = Angle(0, 0, 0)
    count = 0


    while True:

        pipe, button, imu, seq = reader.read_frame()

        now = time.time()
        if now - start_time < calibration_time:
            gyroAngleSum.x += imu.gyro.x
            gyroAngleSum.y += imu.gyro.y
            gyroAngleSum.z += imu.gyro.z
            count += 1
            print(f"Calibrating Gyro...Please keep steady...{calibration_time - now + start_time + 1:.0f} seconds left!")
    
        else:
            gyroBias.x = gyroAngleSum.x / count
            gyroBias.y = gyroAngleSum.y / count
            gyroBias.z = gyroAngleSum.z / count
            gravity.x = imu.accel.x
            gravity.y = imu.accel.y
            gravity.z = imu.accel.z
            print("Calibration complete!")
            print(f"gyroBias.x = {gyroBias.x:.3f}, gyroBias.y = {gyroBias.y:.3f}, gyroBias.z = {gyroBias.z:.3f}")
            print(f"gravity.x = {gravity.x:.3f}, gravity.y = {gravity.y:.3f}, gravity.z = {gravity.z:.3f}")
            return (gyroBias, gravity)
        
        
        
def print_Angle(Name, Angle):
    print(f"{Name}: X:{Angle.x:8.3f}, Y:{Angle.y:8.3f}, Z:{Angle.z:8.3f}")

def main():

    print(f"Listening on {args.port} at {args.baud} baud...")

    # reader = IMUReader(mode="dongle", port=args.port, baud=args.baud)
    reader = IMUReader(mode=readMode, port=args.port, baud=args.baud)


    # last_seq = None

    #global last_time
    last_time = time.time()

    ang_gyro = Angle(0.0, 0.0, 0.0)
    ang_accel = Angle(0.0, 0.0, 0.0)

    bias = calibrate_gyro(reader)

    while True:
        pipe, button, imu, seq = reader.read_frame()
        print_Angle("Accel  ", imu.accel)

        gyro_c = Angle(imu.gyro.x - bias[0].x, imu.gyro.y - bias[0].y, imu.gyro.z - bias[0].z)

        print_Angle("Gyro   ", gyro_c)
        ang_gyro, last_time = get_angle_gyro(ang_gyro, gyro_c, last_time, wrap360 = False)
        print_Angle("Angle_G", ang_gyro)
        ang_accel = get_angle_accel(ang_accel, imu.accel, bias[1])
        print_Angle("Angle_A", ang_accel)
        print_Angle("Gravity", bias[1])



if __name__ == "__main__":
    main()





