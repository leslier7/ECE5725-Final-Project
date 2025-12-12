# imu_adapter.py
import time
import sys
import os
import math

# Add the parent directory to path so we can import dongleparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the ORIGINAL dongleparse (Keep it unchanged)
from dongleparse import DongleReader
from datatypes import Vector3, IMUData

class IMUAdapter:
    """
    Wraps the original DongleReader to return clean IMUData objects.
    """
    def __init__(self, port, baud):
        self.reader = DongleReader(port=port, baud=baud)
        print(f"IMUAdapter connected to {port}")

    def get_data(self) -> IMUData:
        """
        Reads one frame from dongleparse and converts it.
        """
        # pipe, button, imu, seq = self.reader.read_frame()
        # The original dongleparse returns an object with .accel.x, etc.

        while True:

            pipe, button, raw_imu, _ = self.reader.read_frame()
            
            # keep reading the dongle until we get pipe == 2
            if (pipe == 2):
                # Convert to our clean Vector3 format
                accel = Vector3(raw_imu.accel.x, raw_imu.accel.y, raw_imu.accel.z)
                # gyro  = Vector3(raw_imu.gyro.x,  raw_imu.gyro.y,  raw_imu.gyro.z)
                gyro  = Vector3(
                    math.radians(raw_imu.gyro.x),  
                    math.radians(raw_imu.gyro.y),  
                    math.radians(raw_imu.gyro.z)
                )
                break
            
        return IMUData(accel, gyro, time.time()), button

    def close(self):
        self.reader.close()