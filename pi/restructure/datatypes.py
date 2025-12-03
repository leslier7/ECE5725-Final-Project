# datatypes.py
from dataclasses import dataclass

@dataclass
class Vector3:
    """Generic 3D vector for Accel, Gyro, or Euler Angles."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class IMUData:
    """Container for a single frame of sensor data."""
    accel: Vector3
    gyro: Vector3
    timestamp: float

@dataclass
class VisionData:
    """Container for camera tracking results."""
    valid: bool         # True if object found, False if not
    x: float = 0.0      # Normalized X (0.0 to 1.0)
    y: float = 0.0      # Normalized Y (0.0 to 1.0)
    color: str = ""     # Name of the color detected (e.g., "green")
    timestamp: float = 0.0