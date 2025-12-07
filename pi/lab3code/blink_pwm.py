import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

GPIO.setup(16, GPIO.OUT)

freq = 1

p = GPIO.PWM(16, freq)
p.start(50)

code_run = True

while(code_run):

    try:
        usrIn = input('Enter the desired frequency: ')
        if(usrIn == "exit"):
            code_run = False
        else: 
            freq = int(usrIn)
            p.ChangeFrequency(freq)
    except:
        print("Invalid input. Please enter a frequency: ")


p.stop()
GPIO.cleanup()

