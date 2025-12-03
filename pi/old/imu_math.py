# imu_math.py
import math
import time
from imu_reader import IMUReader, Angle


def calibrate_gyro(reader: IMUReader, calib_time: float) -> tuple[Angle, Angle]:
    gyro_sum = Angle(0.0, 0.0, 0.0)
    gyro_bias = Angle(0.0, 0.0, 0.0)
    gravity = Angle(0.0, 0.0, 0.0)
    count = 0

    start_time = time.time()

    while True:
        pipe, button, imu, seq = reader.read_frame()

        now = time.time()
        if now - start_time < calib_time:
            gyro_sum.x += imu.gyro.x
            gyro_sum.y += imu.gyro.y
            gyro_sum.z += imu.gyro.z
            lowpass_filter_Angle(imu.accel, gravity, 0.9)
            count += 1
            left = calib_time - (now - start_time)
            print(
                f"Calibrating Gyro...Please keep steady..."
                f"{left + 1:.0f} seconds left!"
            )
        else:
            gyro_bias.x = gyro_sum.x / count
            gyro_bias.y = gyro_sum.y / count
            gyro_bias.z = gyro_sum.z / count
            
            print("Calibration complete!")
            print_angle("gyroBias", gyro_bias)
            print_angle("gravity", gravity)

            return gyro_bias, gravity


def get_angle_gyro(angle: Angle,
                   gyro: Angle,
                   dt: float,
                   convert_to_degree: bool = True,
                   wrap360: bool = False) -> Angle:
    """Integrate gyro to update angle (in degrees)."""
    if convert_to_degree:
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

    return angle


def get_angle_accel(angle: Angle,
                    accel: Angle,
                    gravity: Angle | None = None,
                    convert_to_degree: bool = True) -> Angle:
    """Compute tilt angle from accelerometer. If gravity is provided, use (accel - gravity)."""
    if gravity is not None:
        ax = accel.x - gravity.x
        ay = accel.y - gravity.y
        az = accel.z - gravity.z
    else:
        ax = accel.x
        ay = accel.y
        az = accel.z

    angle.x = math.atan2(ax, math.sqrt(ay ** 2 + az ** 2))
    angle.y = math.atan2(ay, math.sqrt(ax ** 2 + az ** 2))
    angle.z = math.atan2(az, math.sqrt(ax ** 2 + ay ** 2))

    if convert_to_degree:
        conv = 180.0 / math.pi
        angle.x *= conv
        angle.y *= conv
        angle.z *= conv

    return angle


def complementary_filter(gyro_angle: Angle,
                         accel_angle: Angle,
                         alpha: float = 0.98,
                         wrap360: bool = True) -> Angle:
    """the simplest complementary filter"""

    # average the angle
    fused = Angle(0.0, 0.0, 0.0)
    fused.x = (1.0 - alpha) * accel_angle.x + alpha * gyro_angle.x
    fused.y = (1.0 - alpha) * accel_angle.y + alpha * gyro_angle.y
    fused.z = (1.0 - alpha) * accel_angle.z + alpha * gyro_angle.z

    if wrap360:
        fused.x %= 360.0
        fused.y %= 360.0
        fused.z %= 360.0

    return fused


def print_angle(name: str, angle: Angle) -> None:
    """print Angle type data"""
    print(f"{name}: X:{angle.x:8.3f}, Y:{angle.y:8.3f}, Z:{angle.z:8.3f}")

def format_angle(name: str, angle: Angle) -> str:
    return f"{name}: X:{angle.x:8.3f}, Y:{angle.y:8.3f}, Z:{angle.z:8.3f}"


def lowpass_filter(value, prev_value, alpha):
    return alpha * prev_value + (1 - alpha) * value

def lowpass_filter_Angle(Angle, prev_Angle, alpha) -> None:
    prev_Angle.x = lowpass_filter(Angle.x, prev_Angle.x, alpha)
    prev_Angle.y = lowpass_filter(Angle.y, prev_Angle.y, alpha)
    prev_Angle.z = lowpass_filter(Angle.z, prev_Angle.z, alpha)

