# algorithms/complementary.py
import math
from datatypes import Vector3

class ComplementaryFilter:
    def __init__(self, alpha: float = 0.98):
        """
        alpha: Weight for gyroscope (high pass). 
               Typical value is 0.98. 
               1 - alpha is the weight for accelerometer.
        """
        self.alpha = alpha
        
        # Current orientation in radians
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0 

    def update(self, gyro: Vector3, accel: Vector3, dt: float) -> tuple[float, float, float]:
        """
        Updates the filter and returns (roll, pitch, yaw) in radians.
        """
        
        # 1. Calculate Tilt from Accelerometer (Low Frequency)
        # Note: Accelerometer cannot measure Yaw (Z-rotation) without a magnetometer
        # Using atan2 for better handling of all quadrants
        acc_roll = math.atan2(accel.y, accel.z)
        acc_pitch = math.atan2(-accel.x, math.sqrt(accel.y**2 + accel.z**2))
        
        # 2. Integrate Gyroscope (High Frequency)
        # Predict next angle based on previous angle + speed * time
        self.roll += gyro.x * dt
        self.pitch += gyro.y * dt
        self.yaw += gyro.z * dt  # Yaw will drift because we have no accel correction for Z

        # 3. Fuse Data (The Complementary Formula)
        # Angle = alpha * (Gyro_Integration) + (1-alpha) * (Accel_Reading)
        self.roll = self.alpha * self.roll + (1.0 - self.alpha) * acc_roll
        self.pitch = self.alpha * self.pitch + (1.0 - self.alpha) * acc_pitch
        
        # Note: We don't filter Yaw with accel because gravity doesn't change when you rotate Z.
        
        return self.roll, self.pitch, self.yaw