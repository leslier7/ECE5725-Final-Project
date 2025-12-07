import RPi.GPIO as GPIO
from time import time, sleep
from threading import Thread

GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

pin = GPIO.setup(16, GPIO.OUT)

freq = 1


code_run = True

def consoleIn():
    global code_run
    global freq
    thread_running = True
    while(thread_running):
        try:
            usrIn = input('Enter the desired frequency: ')
            if(usrIn == "exit"):
                code_run = False
                thread_running = False
            else: 
                freq = int(usrIn)
        except:
            print("Invalid input. Please enter a frequency: ")


# Main code
t1 = Thread(target = consoleIn)
t1.start()

#blink the led
while(code_run):
    sleep((1/freq)/2)
    GPIO.output(16, GPIO.HIGH)
    sleep((1/freq)/2)
    GPIO.output(16, GPIO.LOW)

t1.join() # join thread
GPIO.cleanup()

