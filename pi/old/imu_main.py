# imu_main.py
import argparse
import time
import math
import sys


from imu_reader import IMUReader, Angle
from imu_math import (
    calibrate_gyro,
    get_angle_gyro,
    get_angle_accel,
    complementary_filter,
    print_angle,
    format_angle,
    lowpass_filter_Angle,
)
from plotter import RealTimePlotter
from ahrs import Mahony



readMode = "dongle"
calibration_time = 1.0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "port",
        nargs="?",
        default="/dev/tty.usbmodem11101",
        help="Serial port, e.g. /dev/ttyACM0",
    )
    parser.add_argument(
        "-b", "--baud", type=int, default=115200, help="Baud rate"
    )
    parser.add_argument(
        "--hex", action="store_true", help="Print raw frame hex"
    )
    return parser.parse_args()



def print_stable(output: str):
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(output)
    sys.stdout.flush()


def main():
    args = parse_args()
    print(f"Listening on {args.port} at {args.baud} baud...")

    reader = IMUReader(mode=readMode, port=args.port, baud=args.baud)

    accel = Angle(0.0, 0.0, 0.0)
    accel_raw = Angle(0.0, 0.0, 0.0)
    ang_gyro = Angle(0.0, 0.0, 0.0)
    ang_accel = Angle(0.0, 0.0, 0.0)
    ang_comp = Angle(0.0, 0.0, 0.0)

    gyro_bias, gravity = calibrate_gyro(reader, calibration_time)

    last_time = time.time()

    # plotter = RealTimePlotter(max_points=300)

    att3d = Attitude3D()

    mahony = Mahony(kp=1.2, ki=0.0)

    # init screen
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    while True:
        pipe, button, imu, seq = reader.read_frame()

        accel_raw = Angle(imu.accel.x, imu.accel.y, imu.accel.z)
        lowpass_filter_Angle(accel_raw, accel, 0.95)

        gyro_c = Angle(
            imu.gyro.x - gyro_bias.x,
            imu.gyro.y - gyro_bias.y,
            imu.gyro.z - gyro_bias.z,
        )

        now = time.time()
        dt = now - last_time
        last_time = now

        q = mahony.update(gyro_c, accel_raw, dt)
        roll, pitch, yaw = q.to_euler()


        # calculate the angle
        ang_gyro = get_angle_gyro(ang_gyro, gyro_c, dt, wrap360=False)
        ang_accel = get_angle_accel(ang_accel, accel)
        ang_comp = complementary_filter(
            ang_gyro,
            ang_accel,
            alpha=0.98,
            wrap360=False,
        )


        text = []
        text.append(f"Roll:  {roll*180/math.pi:8.3f}")
        text.append(f"Pitch: {pitch*180/math.pi:8.3f}")
        text.append(f"Yaw:   {yaw*180/math.pi:8.3f}")
        text.append("")
        text.append(format_angle("Angle_G", ang_gyro))
        text.append(format_angle("Angle_A", ang_accel))
        text.append(format_angle("Angle_C", ang_comp))
        text.append(format_angle("Gravity", gravity))


        print_stable("\n".join(text))








if __name__ == "__main__":
    main()
