# calibration.py
import time
from datatypes import Vector3
# Note: We pass the 'adapter' in, we don't import it to avoid circular imports

def calibrate_gyro(adapter, duration) -> Vector3:
    """
    Reads data for 'duration' seconds and calculates the average gyro offset.
    """
    print(f"Calibrating Gyro for {duration} seconds... Please stay still.")
    
    start_time = time.time()
    count = 0
    sum_x, sum_y, sum_z = 0.0, 0.0, 0.0

    while (time.time() - start_time) < duration:
        data = adapter.get_data()
        sum_x += data.gyro.x
        sum_y += data.gyro.y
        sum_z += data.gyro.z
        count += 1
    
    if count == 0:
        return Vector3(0,0,0)

    bias = Vector3(sum_x/count, sum_y/count, sum_z/count)
    print(f"Calibration Done. Bias: ({bias.x:.3f}, {bias.y:.3f}, {bias.z:.3f})")
    return bias