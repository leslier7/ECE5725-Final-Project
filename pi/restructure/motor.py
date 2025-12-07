# motor.py
from datatypes import Vector3
import RPi.GPIO as GPIO
from time import time, sleep

# Configs 
pwma_pin = 26
ai1_pin = 5
ai2_pin = 6

pwmb_pin = 13
bi1_pin = 20
bi2_pin = 21


freq = 50
duty_cycle_a = 0
duty_cycle_b = 0

motor_scale = 0.7

code_run = True
control_motor = True # Motor A

class motorControl:
    def __init__(self):

        self.pwma_pin = pwma_pin
        self.ai1_pin = ai1_pin
        self.ai2_pin = ai2_pin

        self.pwmb_pin = pwmb_pin
        self.bi1_pin = bi1_pin
        self.bi2_pin = bi2_pin

        self.freq = freq
        self.duty_cycle_a = duty_cycle_a
        self.duty_cycle_b = duty_cycle_b

        self.motor_scale = motor_scale

        self.PWMA = GPIO.PWM(self.pwma_pin, freq)
        self.PWMB = GPIO.PWM(self.pwmb_pin, freq)

        self.PWMA.start(0)
        self.PWMB.start(0)

        GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

        GPIO.setup(self.pwma_pin, GPIO.OUT)
        GPIO.setup(self.ai1_pin, GPIO.OUT)
        GPIO.setup(self.ai2_pin, GPIO.OUT)

        GPIO.setup(self.pwmb_pin, GPIO.OUT)
        GPIO.setup(self.bi1_pin, GPIO.OUT)
        GPIO.setup(self.bi2_pin, GPIO.OUT)

    def gravity2duty_cycle(self, gravity):
        forward = gravity.x * self.motor_scale
        turn = gravity.y * self.motor_scale
    
        left_dc = forward - turn
        right_dc = forward + turn

        return left_dc, right_dc

    def outputControl(self, left_dc, right_dc, gravity):
        duty_cycle_a, duty_cycle_b = self.gravity2duty_cycle(self, gravity)
        self.PWMA.ChangeDutyCycle(abs(duty_cycle_a))
        self.PWMB.ChangeDutyCycle(abs(duty_cycle_b))

        if (left_dc > 0 & right_dc > 0):
            GPIO.output(ai1_pin, GPIO.HIGH)
            GPIO.output(ai2_pin, GPIO.LOW)
            GPIO.output(bi1_pin, GPIO.HIGH)
            GPIO.output(bi2_pin, GPIO.LOW)
            print("Forwarding...")
        elif (left_dc > 0 & right_dc < 0):
            GPIO.output(ai1_pin, GPIO.HIGH)
            GPIO.output(ai2_pin, GPIO.LOW)
            GPIO.output(bi1_pin, GPIO.HIGH)
            GPIO.output(bi2_pin, GPIO.LOW)
            print("Turing Right...")
        elif (left_dc < 0 & right_dc > 0):
            GPIO.output(ai1_pin, GPIO.HIGH)
            GPIO.output(ai2_pin, GPIO.LOW)
            GPIO.output(bi1_pin, GPIO.HIGH)
            GPIO.output(bi2_pin, GPIO.LOW)
            print("Turing Left...")
        elif (left_dc < 0 & right_dc < 0):
            GPIO.output(ai1_pin, GPIO.HIGH)
            GPIO.output(ai2_pin, GPIO.LOW)
            GPIO.output(bi1_pin, GPIO.HIGH)
            GPIO.output(bi2_pin, GPIO.LOW)
            print("Backwarding...")



