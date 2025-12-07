import RPi.GPIO as GPIO
from time import time, sleep

pwma_pin = 16
ai1_pin = 5
ai2_pin = 6

pwmb_pin = 13
bi1_pin = 20
bi2_pin = 21

GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

GPIO.setup(17,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(22,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(23,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(27,GPIO.IN,pull_up_down=GPIO.PUD_UP)

GPIO.setup(pwma_pin, GPIO.OUT)
GPIO.setup(ai1_pin, GPIO.OUT)
GPIO.setup(ai2_pin, GPIO.OUT)

GPIO.setup(pwmb_pin, GPIO.OUT)
GPIO.setup(bi1_pin, GPIO.OUT)
GPIO.setup(bi2_pin, GPIO.OUT)


freq = 50
duty_cycle_a = 0
duty_cycle_b = 0

code_run = True
control_motor = True # Motor A

def GPIO17_callback(channel):
    print("Button 17 has been pressed!")
    global control_motor
    global pa
    global duty_cycle_a
    global pb
    global duty_cycle_b
    if (control_motor):
        GPIO.output(ai1_pin, GPIO.HIGH)
        GPIO.output(ai2_pin, GPIO.LOW)
        duty_cycle_a = 50
        pa.ChangeDutyCycle(duty_cycle_a)
        print("Motor A spinning Clockwise")
    else:
        GPIO.output(bi1_pin, GPIO.HIGH)
        GPIO.output(bi2_pin, GPIO.LOW)
        duty_cycle_b = 50
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Motor B spinning Clockwise")

def GPIO22_callback(channel):
    print("Button 22 has been pressed!")
    global control_motor
    global pa
    global duty_cycle_a
    global pb
    global duty_cycle_b
    if (control_motor):
        GPIO.output(ai1_pin, GPIO.LOW)
        GPIO.output(ai2_pin, GPIO.HIGH)
        duty_cycle_a = 50
        pa.ChangeDutyCycle(duty_cycle_a)
        print("Motor A spinning Counter Clockwise")
    else:
        GPIO.output(bi1_pin, GPIO.LOW)
        GPIO.output(bi2_pin, GPIO.HIGH)
        duty_cycle_b = 50
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Motor B spinning Counter Clockwise")

def GPIO23_callback(channel):
    print("Button 23 has been pressed!")
    global control_motor
    global pa
    global duty_cycle_a
    global pb
    global duty_cycle_b
    if (control_motor):
        GPIO.output(ai1_pin, GPIO.HIGH)
        GPIO.output(ai2_pin, GPIO.HIGH)
        duty_cycle_a = 0
        pa.ChangeDutyCycle(duty_cycle_a)
        print("Stopping Motor A")
    else:
        GPIO.output(bi1_pin, GPIO.HIGH)
        GPIO.output(bi2_pin, GPIO.HIGH)
        duty_cycle_b = 0
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Stopping Motor B")

    
def GPIO27_callback(channel):
    print("Button 27 has been pressed!")
    global control_motor
    control_motor = not control_motor
    if (control_motor):
        print("Now controling Motor A")
    else:
        print("Now controling Motor B")

GPIO.add_event_detect(17, GPIO.FALLING, callback = GPIO17_callback, bouncetime=200)
GPIO.add_event_detect(22, GPIO.FALLING, callback = GPIO22_callback, bouncetime=200)
GPIO.add_event_detect(23, GPIO.FALLING, callback = GPIO23_callback, bouncetime=200)
GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime=200)

# Initiate
pa = GPIO.PWM(pwma_pin, freq)
pa.start(duty_cycle_a) # Stoped
GPIO.output(ai1_pin, GPIO.HIGH)
GPIO.output(ai2_pin, GPIO.LOW)
print("Clockwise Duty cycle for A: " + str(duty_cycle_a))

pb = GPIO.PWM(pwmb_pin, freq)
pb.start(duty_cycle_b) # Stoped
GPIO.output(bi1_pin, GPIO.HIGH)
GPIO.output(bi2_pin, GPIO.LOW)
print("Clockwise Duty cycle for B: " + str(duty_cycle_b))

try:
    while ( code_run ):
        sleep(1)
    

except KeyboardInterrupt:
    print("Exiting program")

finally:
    pa.stop()
    pb.stop()
    GPIO.cleanup()
