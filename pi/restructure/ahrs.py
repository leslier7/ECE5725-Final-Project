# ahrs.py
import math
from datatypes import Vector3

class Quaternion:
    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def to_euler(self):
        """Returns (roll, pitch, yaw) in radians."""
        # Roll (x-axis rotation)
        sinr = 2 * (self.w * self.x + self.y * self.z)
        cosr = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr, cosr)

        # Pitch (y-axis rotation)
        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny = 2 * (self.w * self.z + self.x * self.y)
        cosy = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny, cosy)

        return roll, pitch, yaw
    
    def gravity_from_quaternion(self) -> Vector3:
        """Convert quaternion to gravity direction vector in body frame."""
        w, x, y, z = self.w, self.x, self.y, self.z

        g_x = 2 * (x*z - w*y)
        g_y = 2 * (w*x + y*z)
        g_z = w*w - x*x - y*y + z*z

        return Vector3(g_x, g_y, g_z)


class MahonyFilter:
    def __init__(self, kp=1.0, ki=0.0):
        self.kp = kp
        self.ki = ki
        self.e_int = Vector3(0, 0, 0) # Integral error
        self.q = Quaternion(1, 0, 0, 0)

    def update(self, gyro: Vector3, accel: Vector3, dt: float):
        q = self.q
        ax, ay, az = accel.x, accel.y, accel.z
        gx, gy, gz = gyro.x, gyro.y, gyro.z

        # Normalize accelerometer
        norm = math.sqrt(ax*ax + ay*ay + az*az)
        if norm == 0: return q
        ax, ay, az = ax/norm, ay/norm, az/norm

        # Estimated direction of gravity
        vx = 2*(q.x*q.z - q.w*q.y)
        vy = 2*(q.w*q.x + q.y*q.z)
        vz = q.w*q.w - q.x*q.x - q.y*q.y + q.z*q.z

        # Error (cross product of measured vs estimated gravity)
        ex = ay*vz - az*vy
        ey = az*vx - ax*vz
        ez = ax*vy - ay*vx

        # Integral Feedback
        self.e_int.x += self.ki * ex * dt
        self.e_int.y += self.ki * ey * dt
        self.e_int.z += self.ki * ez * dt

        # Apply Feedback to Gyro
        gx += self.kp * ex + self.e_int.x
        gy += self.kp * ey + self.e_int.y
        gz += self.kp * ez + self.e_int.z

        # Integrate Quaternion
        # dq/dt = 0.5 * q * omega
        qa, qb, qc, qd = q.w, q.x, q.y, q.z
        q.w += (-qb * gx - qc * gy - qd * gz) * (0.5 * dt)
        q.x += (qa * gx + qc * gz - qd * gy) * (0.5 * dt)
        q.y += (qa * gy - qb * gz + qd * gx) * (0.5 * dt)
        q.z += (qa * gz + qb * gy - qc * gx) * (0.5 * dt)

        # Normalize Quaternion
        norm = math.sqrt(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z)
        q.w /= norm
        q.x /= norm
        q.y /= norm
        q.z /= norm

        # Return Gravity
        gravity = Vector3(vx, vy, vz)

        return q, gravity