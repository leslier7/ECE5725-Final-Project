import RPi.GPIO as GPIO
from time import sleep

pwm_pin = 16
ai1_pin = 5
ai2_pin = 6

GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

GPIO.setup(pwm_pin, GPIO.OUT)
GPIO.setup(ai1_pin, GPIO.OUT)
GPIO.setup(ai2_pin, GPIO.OUT)


freq = 50
duty_cycle = 0

p = GPIO.PWM(pwm_pin, freq)
p.start(duty_cycle) # Stoped
GPIO.output(ai1_pin, GPIO.HIGH)
GPIO.output(ai2_pin, GPIO.LOW)
print("Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)
duty_cycle = 50
p.ChangeDutyCycle(duty_cycle)
GPIO.output(ai1_pin, GPIO.HIGH)
GPIO.output(ai2_pin, GPIO.LOW)
print("Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)
duty_cycle = 99
p.ChangeDutyCycle(duty_cycle)
GPIO.output(ai1_pin, GPIO.HIGH)
GPIO.output(ai2_pin, GPIO.LOW)
print("Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)

## Counter Clock wise
duty_cycle = 0
p.ChangeDutyCycle(duty_cycle)
GPIO.output(ai1_pin, GPIO.LOW)
GPIO.output(ai2_pin, GPIO.HIGH)
print("Counter Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)
duty_cycle = 50
p.ChangeDutyCycle(duty_cycle)
GPIO.output(ai1_pin, GPIO.LOW)
GPIO.output(ai2_pin, GPIO.HIGH)
print("Counter Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)
duty_cycle = 99
p.ChangeDutyCycle(duty_cycle)
GPIO.output(ai1_pin, GPIO.LOW)
GPIO.output(ai2_pin, GPIO.HIGH)
print("Counter Clockwise Duty cycle: " + str(duty_cycle))
sleep(3)


p.stop()
GPIO.cleanup()