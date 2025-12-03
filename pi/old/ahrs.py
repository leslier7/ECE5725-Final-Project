# ahrs.py
import math

class Quaternion:
    def __init__(self, w=1, x=0, y=0, z=0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def to_euler(self):
        # Roll (x-axis rotation)
        sinr = 2 * (self.w * self.x + self.y * self.z)
        cosr = 1 - 2 * (self.x*self.x + self.y*self.y)
        roll = math.atan2(sinr, cosr)

        # Pitch (y-axis rotation)
        sinp = 2 * (self.w*self.y - self.z*self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi/2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny = 2 * (self.w*self.z + self.x*self.y)
        cosy = 1 - 2 * (self.y*self.y + self.z*self.z)
        yaw = math.atan2(siny, cosy)

        return roll, pitch, yaw


# ============================================================
#                        MAHONY
# ============================================================
class Mahony:
    def __init__(self, kp=1.0, ki=0.0):
        self.kp = kp
        self.ki = ki
        self.integralFBx = 0
        self.integralFBy = 0
        self.integralFBz = 0
        self.q = Quaternion()

    def update(self, gyro, accel, dt):
        q = self.q

        ax, ay, az = accel.x, accel.y, accel.z
        gx, gy, gz = gyro.x, gyro.y, gyro.z

        # Normalize accel
        norm = math.sqrt(ax*ax + ay*ay + az*az)
        if norm == 0:
            return q
        ax, ay, az = ax/norm, ay/norm, az/norm

        # Estimated direction of gravity
        vx = 2*(q.x*q.z - q.w*q.y)
        vy = 2*(q.w*q.x + q.y*q.z)
        vz = q.w*q.w - q.x*q.x - q.y*q.y + q.z*q.z

        # Error (cross product)
        ex = ay*vz - az*vy
        ey = az*vx - ax*vz
        ez = ax*vy - ay*vx

        # Integral term
        self.integralFBx += self.ki * ex * dt
        self.integralFBy += self.ki * ey * dt
        self.integralFBz += self.ki * ez * dt

        gx += self.kp*ex + self.integralFBx
        gy += self.kp*ey + self.integralFBy
        gz += self.kp*ez + self.integralFBz

        # Integrate quaternion
        gx, gy, gz = gx*0.5*dt, gy*0.5*dt, gz*0.5*dt

        q.w += (-q.x*gx - q.y*gy - q.z*gz)
        q.x += ( q.w*gx + q.y*gz - q.z*gy)
        q.y += ( q.w*gy - q.x*gz + q.z*gx)
        q.z += ( q.w*gz + q.x*gy - q.y*gx)

        # Normalize
        norm = math.sqrt(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z)
        q.w, q.x, q.y, q.z = q.w/norm, q.x/norm, q.y/norm, q.z/norm

        return q


# ============================================================
#                        MADGWICK
# ============================================================
class Madgwick:
    def __init__(self, beta=0.1):
        self.beta = beta
        self.q = Quaternion()

    def update(self, gyro, accel, dt):
        q = self.q
        ax, ay, az = accel.x, accel.y, accel.z
        gx, gy, gz = gyro.x, gyro.y, gyro.z

        # Normalize accel
        norm = math.sqrt(ax*ax + ay*ay + az*az)
        if norm == 0:
            return q
        ax, ay, az = ax/norm, ay/norm, az/norm

        # Gradient descent — omitted full derivation for clarity
        f1 = 2*(q.x*q.z - q.w*q.y) - ax
        f2 = 2*(q.w*q.x + q.y*q.z) - ay
        f3 = 2*(0.5 - q.x*q.x - q.y*q.y) - az

        J11 = -2*q.y
        J12 = 2*q.z
        J13 = -2*q.w
        J14 = 2*q.x
        J32 = -4*q.x
        J33 = -4*q.y

        step_x = J11*f1 + J12*f2 + J13*f3
        step_y = J14*f1 + J32*f2 + J33*f3
        step_z = 0  # simplified
        step_w = 0  # simplified

        norm = math.sqrt(step_x*step_x + step_y*step_y)
        step_x, step_y = step_x/norm, step_y/norm

        gx -= self.beta * step_x
        gy -= self.beta * step_y

        # Integrate quaternion
        gx, gy, gz = gx*0.5*dt, gy*0.5*dt, gz*0.5*dt

        q.w += (-q.x*gx - q.y*gy - q.z*gz)
        q.x += ( q.w*gx + q.y*gz - q.z*gy)
        q.y += ( q.w*gy - q.x*gz + q.z*gx)
        q.z += ( q.w*gz + q.x*gy - q.y*gx)

        # Normalize
        norm = math.sqrt(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z)
        q.w, q.x, q.y, q.z = q.w/norm, q.x/norm, q.y/norm, q.z/norm

        return q
