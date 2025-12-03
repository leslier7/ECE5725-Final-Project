# vision.py
import cv2
import numpy as np
import time
from datatypes import VisionData

class CameraTracker:

    def __init__(self, camera_id=0, width=320, height=240):
        # Initialize Camera
        # Changing that to LibCamera when applying on Pi
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            print(f"Warning: Camera {camera_id} failed to open.")
        
        # Set Resolution (Low res is better for Pi)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Color Configuration Dictionary
        # Format: "name": (Lower_HSV, Upper_HSV)
        self.colors = {
            "green": (np.array([40, 40, 40]), np.array([80, 255, 255])),
            # Red is tricky in HSV (it wraps around 0). This covers 170-180 range.
            "red":   (np.array([170, 100, 100]), np.array([180, 255, 255])) 
        }


    def get_position(self, target_color="green") -> VisionData:
        """
        Reads a frame and finds the position of the specified color.
        """
        success, frame = self.cap.read()
        if not success:
            return VisionData(valid=False, timestamp=time.time())

        # Preprocessing
        frame = cv2.flip(frame, 1)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            
        lower, upper = self.colors[target_color]

        # Masking
        mask = cv2.inRange(hsv, lower, upper) # Thresholding the color
        mask = cv2.erode(mask, None, iterations=2) # erode the color, cut the edge of the color
        mask = cv2.dilate(mask, None, iterations=2)

        # Contours
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            # Find biggest blob
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if radius > 10:
                # Normalize coordinates (0.0 to 1.0)
                h, w, _ = frame.shape
                norm_x = x / w
                norm_y = y / h
                
                # Optional: Show debug window
                # cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                # cv2.imshow(f"Tracker - {target_color}", frame)
                cv2.waitKey(1)

                return VisionData(True, norm_x, norm_y, target_color, time.time())

        # If nothing found, show frame anyway for debugging
        # cv2.imshow(f"Tracker - {target_color}", frame)
        cv2.waitKey(1)
        
        return VisionData(valid=False, timestamp=time.time())

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()