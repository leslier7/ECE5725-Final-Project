# display.py
import sys
import math

def print_stable_output(roll, pitch, yaw, fps, gravity, VisionData):
    """
    Clears the terminal and prints the angles.
    """
    # Convert radians to degrees
    r_deg = math.degrees(roll)
    p_deg = math.degrees(pitch)
    y_deg = math.degrees(yaw)

    # ANSI Escape codes for clearing screen and moving cursor to Home
    sys.stdout.write("\033[H") 
    
    output = (
        "================================\n"
        "        IMU Orientation         \n"
        "================================\n"
        f" Roll  (X): {r_deg:8.2f} deg\n"
        f" Pitch (Y): {p_deg:8.2f} deg\n"
        f" Yaw   (Z): {y_deg:8.2f} deg\n"
        "--------------------------------\n"
        f" Rate     : {fps:8.1f} Hz \n"
        f" Gravity  : {gravity.x:6.2f},{gravity.y:6.2f},{gravity.z:6.2f}\n"
        f" Position : {VisionData.x:8.2f}, {VisionData.y:8.2f}\n"
        "================================\n"
    )
    
    sys.stdout.write(output)
    sys.stdout.flush()

def clear_terminal():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()