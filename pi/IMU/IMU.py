import serial
import time

# init the serial port
ser = serial.Serial('/dev/tty.usbmodem101', 115200)

a_x = a_y = a_z = r_x = r_y = r_z = 0.0
angle_x = angle_y = angle_z = 0.0
calibration_time = 10.0
start_time = time.time()
rx_bias = ry_bias = rz_bias = 0.0

def handle_message(inputLine):
    global a_x, a_y, a_z, r_x, r_y, r_z

    # check for invalid signal
    parts = inputLine.split()
    if (len(parts) < 6):
        return
    
    if "accel" in inputLine:
        try:
            a_x = float(parts[1].split(":")[1])
            a_y = float(parts[3].split(":")[1])
            a_z = float(parts[5].split(":")[1])
        # if invalid value appears, don't use that
        except:
            return
        # print(f"Accel: x:{a_x:8.3f}, y:{a_y:8.3f}, z:{a_z:8.3f}")
    elif "gyro" in inputLine:
        try:
            r_x = float(parts[1].split(":")[1])
            r_y = float(parts[3].split(":")[1])
            r_z = float(parts[5].split(":")[1])
        except:
            return
        # print(f"Gyro:  x:{r_x:8.3f}, y:{r_y:8.3f}, z:{r_z:8.3f}")

def get_angle():
    global angle_x, angle_y, angle_z
    global last_time

    now = time.time()
    dt = now - last_time
    last_time = now

    angle_x += r_x * dt
    angle_y += r_y * dt
    angle_z += r_z * dt

def calibrate_gyro():
    global rx_bias, ry_bias, rz_bias
    global r_x, r_y, r_z
    rx_sum = ry_sum = rz_sum = 0.0
    count = 0

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        if not line:
            continue

        handle_message(line)
        now = time.time()
        if now - start_time < calibration_time:
            if "gyro" in line:
                rx_sum += r_x
                ry_sum += r_y
                rz_sum += r_z
                count += 1
                print(f"Calibrating Gyro...Please keep steady...{calibration_time - now + start_time + 1:.0f} seconds left!")
        else:
            rx_bias = rx_sum / count
            ry_bias = ry_sum / count
            rz_bias = rz_sum / count
            print("Calibration complete!")
            print(f"rx_bias = {rx_bias:.3f}, ry_bias = {ry_bias:.3f}, rz_bias = {rz_bias:.3f}")
            break

calibrate_gyro()

last_time = time.time()

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()

    if not line:
        continue
    
    # convert received data -> float
    handle_message(line)

    if "accel" in line:
        # print(f"Accel: x:{a_x:8.3f}, y:{a_y:8.3f}, z:{a_z:8.3f}")
        continue

    elif "gyro" in line:
        r_x -= rx_bias
        r_y -= ry_bias
        r_z -= rz_bias
        # print(f"Gyro:  x:{r_x:8.3f}, y:{r_y:8.3f}, z:{r_z:8.3f}")
        get_angle()
        print(f"Angle X:{angle_x:8.3f},  Y:{angle_y:8.3f},  Z:{angle_z:8.3f}")








