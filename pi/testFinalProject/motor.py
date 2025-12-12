# motor.py
from datatypes import Vector3
import RPi.GPIO as GPIO
from time import sleep

# --- Pin Configuration ---
# Motor A (Left Motor)
PWMA_PIN = 26 
AI1_PIN = 5
AI2_PIN = 6

# Motor B (Right Motor)
PWMB_PIN = 13
BI1_PIN = 20
BI2_PIN = 16

FREQ = 50
MOTOR_SCALE = 0.7 # Scale factor for converting gravity/angle to speed
TURN_SCALE = 0.5 # Scale factor for turn

GPIO.setmode(GPIO.BCM) 

class MotorDriver:
    def __init__(self):
       
        # --- Pin Assignments ---
        self.pwma_pin = PWMA_PIN
        self.ai1_pin = AI1_PIN
        self.ai2_pin = AI2_PIN
        self.pwmb_pin = PWMB_PIN
        self.bi1_pin = BI1_PIN
        self.bi2_pin = BI2_PIN
        self.motor_scale = MOTOR_SCALE
        self.turn_scale = TURN_SCALE

        # --- Pin Setup ---
        GPIO.setup(self.pwma_pin, GPIO.OUT)
        GPIO.setup(self.ai1_pin, GPIO.OUT)
        GPIO.setup(self.ai2_pin, GPIO.OUT)
        GPIO.setup(self.pwmb_pin, GPIO.OUT)
        GPIO.setup(self.bi1_pin, GPIO.OUT)
        GPIO.setup(self.bi2_pin, GPIO.OUT)
        
        # --- PWM Setup ---
        self.PWMA = GPIO.PWM(self.pwma_pin, FREQ)
        self.PWMB = GPIO.PWM(self.pwmb_pin, FREQ)
        
        self.PWMA.start(0) # Start PWM at 0% duty cycle
        self.PWMB.start(0)


    def _set_motor_direction(self, motor_name, direction):
        """
        Helper function to set motor direction.
        direction: 1 (Forward), -1 (Backward), 0 (Stop)
        """
        if motor_name == 'A':
            in1, in2 = self.ai1_pin, self.ai2_pin
        else: # motor_name == 'B'
            in1, in2 = self.bi1_pin, self.bi2_pin

        if direction == 1:
            # Forward
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        elif direction == -1:
            # Backward
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
        else:
            # Stop (Brake/Coast depends on driver chip wiring)
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)

    def convert2Feedback360(self, left_dc, right_dc, button_stop):

        # dutyCycle 6.4 - 7.4: ClockWise
        # dutyCycle 7.4 - 7.6: Stop
        # dutyCycle 7.6 - 8.6: CounterClockWise

        # for motor A (left), clockwise -> backwards
        # for motor B (right), clockwise -> forwards

        # range: -5 ~ 5
        
        left_dc = -left_dc
        # right_dc = -right_dc
            
        left_dc = 7.1 + 1 * left_dc * (0 if button_stop == 1 else 1)
        right_dc = 7.1 + 1 * right_dc * (0 if button_stop == 1 else 1)

        return left_dc, right_dc

    def control_from_gravity(self, gravity: Vector3, button_stop):
        
        # Calculate base control signals
        forward = gravity.x
        turn = gravity.y
        
        # dutyCycle 6.4 - 7.4: ClockWise
        # dutyCycle 7.4 - 7.6: Stop
        # dutyCycle 7.6 - 8.6: CounterClockWise
        
        # forward_dc = int(forward * 5)
        forward_dc = forward

        # if abs(turn) <= 0.2:
        #     turn_dc = 0 * self.turn_scale
        # elif 0.2 < abs(turn) <= 0.4:
        #     turn_dc = 25 * self.turn_scale
        # elif 0.4 < abs(turn) <= 0.6:
        #     turn_dc = 50 * self.turn_scale
        # elif 0.6 < abs(turn) <= 0.8:
        #     turn_dc = 75 * self.turn_scale
        # elif 0.8 < abs(turn) <= 1:
        #     turn_dc = 100 * self.turn_scale

        # turn_dc = int(turn * 5) * self.turn_scale

        turn_dc = turn * self.turn_scale

        if forward >= 0:
            left_dc = forward_dc + turn_dc
            right_dc = forward_dc - turn_dc
        else: # forward < 0
            left_dc = forward_dc - turn_dc
            right_dc = forward_dc + turn_dc

        
        left_abs_dc = abs(left_dc)
        right_abs_dc = abs(right_dc)
        dc_max = max(left_abs_dc, right_abs_dc)

        # Normalization
        if dc_max >= 1:
            left_dc = left_dc / dc_max * 1
            right_dc = right_dc / dc_max * 1

        left_dc, right_dc = self.convert2Feedback360(left_dc, right_dc, button_stop)

        # --- Left Motor Control ---
        self.PWMA.ChangeDutyCycle(left_dc)
        # self._set_motor_direction('A', 1 if left_dc >= 0 else -1)
        
        # --- Right Motor Control ---
        self.PWMB.ChangeDutyCycle(right_dc)
        # self._set_motor_direction('B', 1 if right_dc >= 0 else -1)

        duty_cycle = Vector3(left_dc, right_dc, 0.0)

        return duty_cycle

    
    def control_from_gravity3(self, gravity: Vector3):
        
        # Calculate base control signals
        forward = gravity.x
        turn = gravity.y
        # if abs(forward) <= 0.2:
        #     forward_dc = 0
        # elif 0.2 < abs(forward) <= 0.4:
        #     forward_dc = 25
        # elif 0.4 < abs(forward) <= 0.6:
        #     forward_dc = 50
        # elif 0.6 < abs(forward) <= 0.8:
        #     forward_dc = 75
        # elif 0.8 < abs(forward) <= 1:
        #     forward_dc = 100
        
        forward_dc = int(forward * 5) * 25

        # if abs(turn) <= 0.2:
        #     turn_dc = 0 * self.turn_scale
        # elif 0.2 < abs(turn) <= 0.4:
        #     turn_dc = 25 * self.turn_scale
        # elif 0.4 < abs(turn) <= 0.6:
        #     turn_dc = 50 * self.turn_scale
        # elif 0.6 < abs(turn) <= 0.8:
        #     turn_dc = 75 * self.turn_scale
        # elif 0.8 < abs(turn) <= 1:
        #     turn_dc = 100 * self.turn_scale

        turn_dc = int(turn * 5) * 25 * self.turn_scale

        if forward >= 0:
            left_dc = forward_dc + turn_dc
            right_dc = forward_dc - turn_dc
        else: # forward < 0
            left_dc = forward_dc - turn_dc
            right_dc = forward_dc + turn_dc

        
        left_abs_dc = abs(left_dc)
        right_abs_dc = abs(right_dc)
        dc_max = max(left_abs_dc, right_abs_dc)

        # Normalization
        if dc_max >= 100:
            left_abs_dc = left_abs_dc / dc_max * 100
            right_abs_dc = right_abs_dc / dc_max * 100

        # --- Left Motor Control ---
        self.PWMA.ChangeDutyCycle(left_abs_dc)
        self._set_motor_direction('A', 1 if left_dc >= 0 else -1)
        
        # --- Right Motor Control ---
        self.PWMB.ChangeDutyCycle(right_abs_dc)
        self._set_motor_direction('B', 1 if right_dc >= 0 else -1)

        duty_cycle = Vector3(left_dc, right_dc, 0.0)

        return duty_cycle


    def control_from_gravity2(self, gravity: Vector3):
        
        # Calculate base control signals
        forward = gravity.x
        turn = gravity.y
        if forward >= 0:
            left_dc = forward + turn
            right_dc = forward - turn
        else: # forward < 0
            left_dc = forward - turn
            right_dc = forward + turn

        left_abs_dc = 1.5 * abs(left_dc)
        right_abs_dc = 1.5 * abs(right_dc)
        dc_max = max(left_abs_dc, right_abs_dc)

        # Normalization
        if dc_max >= 1:
            left_abs_dc = left_abs_dc / dc_max
            right_abs_dc = right_abs_dc / dc_max

        # --- Left Motor Control ---
        left_abs_dc *= 100
        self.PWMA.ChangeDutyCycle(left_abs_dc)
        self._set_motor_direction('A', 1 if left_dc >= 0 else -1)
        
        # --- Right Motor Control ---
        right_abs_dc *= 100
        self.PWMB.ChangeDutyCycle(right_abs_dc)
        self._set_motor_direction('B', 1 if right_dc >= 0 else -1)

        duty_cycle = Vector3(left_dc, right_dc, 0.0)

        return duty_cycle


    def control_from_gravity1(self, gravity: Vector3):
        
        # Calculate base control signals
        forward = gravity.x * self.motor_scale
        turn = gravity.y * self.motor_scale
    
        # Differential drive calculation
        left_dc = forward - turn
        right_dc = forward + turn

        # --- Left Motor Control ---
        left_abs_dc = 100 * abs(left_dc)
        self.PWMA.ChangeDutyCycle(left_abs_dc)
        self._set_motor_direction('A', 1 if left_dc >= 0 else -1)
        
        # --- Right Motor Control ---
        right_abs_dc = 100 * abs(right_dc)
        self.PWMB.ChangeDutyCycle(right_abs_dc)
        self._set_motor_direction('B', 1 if right_dc >= 0 else -1)

        duty_cycle = Vector3(100 * left_dc, 100 * right_dc, 0.0)

        return duty_cycle


    def stop_and_cleanup(self):
        
        self.PWMA.stop()
        self.PWMB.stop()
        # Note: GPIO.cleanup is usually called in the main program's finally block.