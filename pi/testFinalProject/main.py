# main.py
import time
import argparse
import config

# Import modules
from datatypes import Vector3
from imu_adapter import IMUAdapter
from ahrs import MahonyFilter
from calibration import calibrate_gyro
from display import print_stable_output, clear_terminal
from complementary import ComplementaryFilter
# from vision import CameraTracker
import RPi.GPIO as GPIO
from motor import MotorDriver

def main():

    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", default=config.SERIAL_PORT, help="Port")
    args = parser.parse_args()


    # =========================================
    # Init Sensors
    # =========================================

    # Init the Camera
    # try:
    #     print(f"Initializing Camera {config.CAMERA_ID}...")
    #     tracker = CameraTracker(
    #         camera_id=config.CAMERA_ID, 
    #         width=config.VISION_WIDTH, 
    #         height=config.VISION_HEIGHT
    #     )
    # except Exception as e:
    #     print(f"Camera init failed: {e}")
    #     tracker = None  # If there is no camera, the code can still run

    # Init the IMU
    try:
        adapter = IMUAdapter(port=args.port, baud=config.BAUD_RATE)
    except Exception as e:
        print(f"IMU connect failed: {e}")
        return # if IMU fails, the code should not run anymore

    # Init the Motor Driver
    print("Initializing Motor Driver...")
    try:
        motor_control = MotorDriver()
    except Exception as e:
        print(f"Motor driver init failed: {e}")
        motor_control = None
    

    
    # =========================================
    # Init Algorithms
    # =========================================

    # Init Filter Algorithms
    mahony = MahonyFilter(kp=config.MAHONY_KP, ki=config.MAHONY_KI)
    comp_filter = ComplementaryFilter(alpha=config.COMPLEMENTARY_ALPHA)

    # Init Calibration Algorithms
    gyro_bias = calibrate_gyro(adapter, config.CALIBRATION_TIME)

    # Output the Filter Algorithm
    print(f"Using {config.FILTER_MODE} Filter Algorithm")

    time.sleep(1)
    


    # =========================================
    # Main Loop
    # =========================================

    # Clear screen before loop
    clear_terminal()
    last_time = time.time()

    BUTTON_STOP = False

    # Main Loop
    try:
        while True:

            # --- Get Sensor Data ---
            imu_data, button = adapter.get_data()
            # vis_data = Vector3()
            # if tracker: # Only track when Camera is connected
            #     vis_data = tracker.get_position(target_color=config.TARGET_COLOR)

            if button:
                BUTTON_STOP = not BUTTON_STOP
            
            # --- Time Calculation --- 
            now = time.time()
            dt = now - last_time
            last_time = now


            # --- Correct Gyro Bias ---
            corrected_gyro = Vector3(
                imu_data.gyro.x - gyro_bias.x,
                imu_data.gyro.y - gyro_bias.y,
                imu_data.gyro.z - gyro_bias.z
            )

            # --- Update Filter Algorithm ---
            if config.FILTER_MODE == 'Mahony':
                q, gravity = mahony.update(corrected_gyro, imu_data.accel, dt)
                roll, pitch, yaw = q.to_euler()
            elif config.FILTER_MODE == 'Complementary':
                roll, pitch, yaw = comp_filter.update(corrected_gyro, imu_data.accel, dt)
                gravity = imu_data.accel

            # --- Motor Control ---
            if motor_control:
                duty_cycle = motor_control.control_from_gravity(gravity, BUTTON_STOP)

            # --- Display ---
            # Avoid division by zero for fps
            fps = 1.0 / dt if dt > 0 else 0 
            print_stable_output(roll, pitch, yaw, fps, gravity, duty_cycle, BUTTON_STOP)

    except KeyboardInterrupt:
        print("\nStopping...")
        adapter.close()
        # if tracker:  
        #     tracker.close()

    finally:
        if motor_control:
            motor_control.stop_and_cleanup()
        GPIO.cleanup()
        print("\nGPIO cleaned!")

if __name__ == "__main__":
    main()