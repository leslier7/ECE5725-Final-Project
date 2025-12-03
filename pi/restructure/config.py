# config.py

# Serial Port Settings
SERIAL_PORT = "/dev/tty.usbmodem11101"  # Change this for your Mac
BAUD_RATE = 115200

# Algorithm Settings
MAHONY_KP = 1.2
MAHONY_KI = 0.0

# Calibration Settings
CALIBRATION_TIME = 2.0  # seconds

# Complementary Settings
COMPLEMENTARY_ALPHA = 0.98

# Filter Algorithms: Mahony or Complementary
FILTER_MODE = 'Mahony'

# Camera Settings
CAMERA_ID = 1           # On Mac, set this to 1
VISION_WIDTH = 320      # Low resolution for better FPS on Pi
VISION_HEIGHT = 240
TARGET_COLOR = "green"  # Default color to track
