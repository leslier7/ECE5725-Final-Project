import argparse
import serial
import time
import math
from dataclasses import dataclass
from dongleparse import DongleReader, Sensor, IMU

@dataclass
class Angle:
    x: float
    y: float
    z: float

parser = argparse.ArgumentParser()
parser.add_argument("port", nargs="?", default="/dev/ttyACM0", help="Serial port, e.g. /dev/ttyACM0")
parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
parser.add_argument("--hex", action="store_true", help="Print raw frame hex")
args = parser.parse_args()

# init the serial port
#ser = serial.Serial('/dev/tty.usbmodem101', 115200)

a_x = a_y = a_z = r_x = r_y = r_z = 0.0
angle_x = angle_y = angle_z = 0.0
calibration_time = 10.0
start_time = time.time()
rx_bias = ry_bias = rz_bias = 0.0

def handle_message(inputLine):
    global a_x, a_y, a_z, r_x, r_y, r_z

    # check for invalid signal
    parts = inputLine.split()
    if (len(parts) < 6):
        return
    
    if "accel" in inputLine:
        try:
            a_x = float(parts[1].split(":")[1])
            a_y = float(parts[3].split(":")[1])
            a_z = float(parts[5].split(":")[1])
        # if invalid value appears, don't use that
        except:
            return
        # print(f"Accel: x:{a_x:8.3f}, y:{a_y:8.3f}, z:{a_z:8.3f}")
    elif "gyro" in inputLine:
        try:
            r_x = float(parts[1].split(":")[1])
            r_y = float(parts[3].split(":")[1])
            r_z = float(parts[5].split(":")[1])
        except:
            return
        # print(f"Gyro:  x:{r_x:8.3f}, y:{r_y:8.3f}, z:{r_z:8.3f}")

def get_angle(angle, gyro, last_time, gyro_in_radians: bool = True, wrap360: bool = True):
    #global angle_x, angle_y, angle_z
    
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

def calibrate_gyro(dongle):
    # global rx_bias, ry_bias, rz_bias
    # global r_x, r_y, r_z
    rx_sum = ry_sum = rz_sum = 0.0
    count = 0

    while True:
        # line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        # if not line:
        #     continue

        # handle_message(line)

        pipe, button, imu, seq = dongle.read_frame()

        now = time.time()
        if now - start_time < calibration_time:
            rx_sum += imu.gyro.x
            ry_sum += imu.gyro.y
            rz_sum += imu.gyro.z
            count += 1
            print(f"Calibrating Gyro...Please keep steady...{calibration_time - now + start_time + 1:.0f} seconds left!")
            # if "gyro" in line:
            #     rx_sum += r_x
            #     ry_sum += r_y
            #     rz_sum += r_z
            #     count += 1
            #     print(f"Calibrating Gyro...Please keep steady...{calibration_time - now + start_time + 1:.0f} seconds left!")
        else:
            rx_bias = rx_sum / count
            ry_bias = ry_sum / count
            rz_bias = rz_sum / count
            print("Calibration complete!")
            print(f"rx_bias = {rx_bias:.3f}, ry_bias = {ry_bias:.3f}, rz_bias = {rz_bias:.3f}")
            bias = Angle(rx_bias, ry_bias, rz_bias)
            return bias

# calibrate_gyro()

def main():
    ser = serial.Serial(args.port, args.baud)
    print(f"Listening on {args.port} at {args.baud} baud...")

    dr = DongleReader(port=args.port, baud=args.baud)

    last_seq = None

    #global last_time
    last_time = time.time()

    ang = Angle(0.0, 0.0, 0.0)

    bias = calibrate_gyro(dr)

    while True:
        pipe, button, imu, seq = dr.read_frame()
        print(f"Accel: x:{imu.accel.x:8.3f}, y:{imu.accel.y:8.3f}, z:{imu.accel.z:8.3f}")

        gyro_c = Angle(imu.gyro.x - bias.x, imu.gyro.y - bias.y, imu.gyro.z - bias.z)

        print(f"Gyro:  x:{gyro_c.x:8.3f}, y:{gyro_c.y:8.3f}, z:{gyro_c.z:8.3f}")
        ang, last_time = get_angle(ang, gyro_c, last_time)
        print(f"Angle X:{ang.x:8.3f},  Y:{ang.y:8.3f},  Z:{ang.z:8.3f}")
        # line = ser.readline().decode('utf-8', errors='ignore').strip()

        # if not line:
        #     continue
        
        # # convert received data -> float
        # handle_message(line)

        # if "accel" in line:
        #     # print(f"Accel: x:{a_x:8.3f}, y:{a_y:8.3f}, z:{a_z:8.3f}")
        #     continue

        # elif "gyro" in line:
        #     r_x -= rx_bias
        #     r_y -= ry_bias
        #     r_z -= rz_bias
        #     # print(f"Gyro:  x:{r_x:8.3f}, y:{r_y:8.3f}, z:{r_z:8.3f}")
        #     get_angle(last_time)
        #     print(f"Angle X:{angle_x:8.3f},  Y:{angle_y:8.3f},  Z:{angle_z:8.3f}")


if __name__ == "__main__":
    main()





