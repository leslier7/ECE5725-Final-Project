import pygame,pigame
from pygame.locals import *
import os
import sys
import time
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM) #set to use GPIO pin numbers

# os.putenv('SDL_VIDEODRV','fbcon')
# os.putenv('SDL_FBDEV', '/dev/fb1')
# os.putenv('SDL_MOUSEDRV','dummy')
# os.putenv('SDL_MOUSEDEV','/dev/null')
# os.putenv('DISPLAY','')




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
        addValue(left_history, ('CLK', int(time.time()-start_time)))
    else:
        GPIO.output(bi1_pin, GPIO.HIGH)
        GPIO.output(bi2_pin, GPIO.LOW)
        duty_cycle_b = 50
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Motor B spinning Clockwise")
        addValue(right_history, ('CLK', int(time.time()-start_time)))

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
        addValue(left_history, ('Counter-CLK', int(time.time()-start_time)))
    else:
        GPIO.output(bi1_pin, GPIO.LOW)
        GPIO.output(bi2_pin, GPIO.HIGH)
        duty_cycle_b = 50
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Motor B spinning Counter Clockwise")
        addValue(right_history, ('Counter-CLK', int(time.time()-start_time)))

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
        addValue(left_history, ('Stop', int(time.time()-start_time)))
    else:
        GPIO.output(bi1_pin, GPIO.HIGH)
        GPIO.output(bi2_pin, GPIO.HIGH)
        duty_cycle_b = 0
        pb.ChangeDutyCycle(duty_cycle_b)
        print("Stopping Motor B")
        addValue(right_history, ('Stop', int(time.time()-start_time)))

    
def GPIO27_callback(channel):
    print("Button 27 has been pressed!")
    global control_motor
    control_motor = not control_motor
    if (control_motor):
        print("Now controling Motor A")
    else:
        print("Now controling Motor B")





#Colours
WHITE = (255,255,255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

pygame.init()
pitft = pigame.PiTft()
lcd = pygame.display.set_mode((320, 240))
lcd.fill(WHITE)

font_big = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 25)
font_xtrasmall = pygame.font.Font(None, 20)




# Touchscreen Buttons
touch_buttons_panic = {'Quit':(280,215), 'Panic':(160,120)}
touch_buttons_resume = {'Quit':(280,215), 'Resume':(160,120)}

history_labels = {'Left History': (60, 60), 'Right History':(260, 60)}

left_history_position = [(60, 140), (60, 120), (60, 100)]
right_history_position = [(260, 140), (260, 120), (260, 100)]

# set up empty lists
left_history = []
right_history = []


# Draw panic circle
pygame.draw.circle(lcd, RED, touch_buttons_panic['Panic'], 40)

for k,v in touch_buttons_panic.items():
    text_surface = font_small.render('%s'%k, True, BLACK)
    rect = text_surface.get_rect(center=v)
    lcd.blit(text_surface, rect)
          
##pygame.display.update()
pygame.display.flip()

freq = 50
duty_cycle_a = 0
duty_cycle_b = 0

code_run = True
control_motor = True # Motor A

panic_color = RED
panic_text = 'STOP'
panic_value = False

def addValue(list, value):
    if(len(list) > 2):
        list.pop(0)
    list.append(value)

history_state = {'duty_cycle_a':0, 'duty_cycle_b':0, 'ai1':GPIO.HIGH, 'ai2':GPIO.LOW, 'bi1':GPIO.HIGH, 'bi2':GPIO.LOW}


try:

    freq = 50
    duty_cycle_a = 0
    duty_cycle_b = 0

    GPIO.setup(17,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(22,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(23,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27,GPIO.IN,pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(17, GPIO.FALLING, callback = GPIO17_callback, bouncetime=200)
    GPIO.add_event_detect(22, GPIO.FALLING, callback = GPIO22_callback, bouncetime=200)
    GPIO.add_event_detect(23, GPIO.FALLING, callback = GPIO23_callback, bouncetime=200)
    GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime=200)

    pwma_pin = 16
    ai1_pin = 5
    ai2_pin = 6

    pwmb_pin = 13
    bi1_pin = 20
    bi2_pin = 21

    
    GPIO.setup(pwma_pin, GPIO.OUT)
    GPIO.setup(ai1_pin, GPIO.OUT)
    GPIO.setup(ai2_pin, GPIO.OUT)

    GPIO.setup(pwmb_pin, GPIO.OUT)
    GPIO.setup(bi1_pin, GPIO.OUT)
    GPIO.setup(bi2_pin, GPIO.OUT)

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

    start_time = time.time()
    while ( code_run ):
        lcd.fill(WHITE)
        pitft.update()
        for event in pygame.event.get():
            if(event.type is MOUSEBUTTONDOWN):
                x,y = pygame.mouse.get_pos()
                #print(x,y)
                print("Touch at " + str(x) + ", " + str(y))
                if(x > 260 and y > 200):
                    print("Quitting")
                    code_run = False
                elif (x > 120 and x < 200 and y > 80 and y < 160):
                    print("Stop pressed")
                    if(panic_value == False):
                        panic_color = GREEN
                        panic_text = 'Resume'
                        panic_value = True
                        
                        addValue(left_history, ('Stop', int(time.time()-start_time)))
                        addValue(right_history, ('Stop', int(time.time()-start_time)))
                        history_state['duty_cycle_a'] = duty_cycle_a
                        history_state['duty_cycle_b'] = duty_cycle_b
                        history_state['ai1'] = GPIO.input(ai1_pin)
                        history_state['ai2'] = GPIO.input(ai2_pin)
                        history_state['bi1'] = GPIO.input(bi1_pin)
                        history_state['bi2'] = GPIO.input(bi2_pin)
                        print(history_state)
                        # Stop motor A
                        GPIO.output(ai1_pin, GPIO.HIGH)
                        GPIO.output(ai2_pin, GPIO.HIGH)
                        duty_cycle_a = 0
                        pa.ChangeDutyCycle(duty_cycle_a)
                        print("Stopping Motor A")

                        #Stop motor b
                        GPIO.output(bi1_pin, GPIO.HIGH)
                        GPIO.output(bi2_pin, GPIO.HIGH)
                        duty_cycle_b = 0
                        pb.ChangeDutyCycle(duty_cycle_b)
                        print("Stopping Motor B")
                    else:
                        panic_color = RED
                        panic_text = 'STOP'
                        panic_value = False

                        addValue(left_history, ('Resume', int(time.time()-start_time)))
                        addValue(right_history, ('Resume', int(time.time()-start_time)))

                        duty_cycle_a = history_state['duty_cycle_a']
                        duty_cycle_b = history_state['duty_cycle_b']
                        GPIO.output(ai1_pin, history_state['ai1'])
                        GPIO.output(ai2_pin, history_state['ai2'])
                        GPIO.output(bi1_pin, history_state['bi1'])
                        GPIO.output(bi2_pin, history_state['bi2'])
                        pa.ChangeDutyCycle(duty_cycle_a)
                        pb.ChangeDutyCycle(duty_cycle_b)
                        
                    print(left_history)
        
        # Draw panic circle
        pygame.draw.circle(lcd, panic_color, touch_buttons_panic['Panic'], 40)
        if (panic_value == True):
            for k,v in touch_buttons_resume.items():
                text_surface = font_small.render('%s'%k, True, BLACK)
                rect = text_surface.get_rect(center=v)
                lcd.blit(text_surface, rect)
        else:
            for k,v in touch_buttons_panic.items():
                text_surface = font_small.render('%s'%k, True, BLACK)
                rect = text_surface.get_rect(center=v)
                lcd.blit(text_surface, rect)

        # Draw history labels
        for k,v in history_labels.items():
                text_surface = font_xtrasmall.render('%s'%k, True, BLACK)
                rect = text_surface.get_rect(center=v)
                lcd.blit(text_surface, rect)

        i=0
        for k in left_history:
            string = k[0] + ": " + str(k[1])
            text_surface = font_xtrasmall.render(string, True, BLACK)
            rect = text_surface.get_rect(center=left_history_position[i])
            lcd.blit(text_surface, rect)
            i += 1

        i=0
        for k in right_history:
            string = k[0] + ": " + str(k[1])
            text_surface = font_xtrasmall.render(string, True, BLACK)
            rect = text_surface.get_rect(center=right_history_position[i])
            lcd.blit(text_surface, rect)
            i += 1
        pygame.display.flip()

    

except KeyboardInterrupt:
    print("Exiting program")

finally:
    del(pitft)
    pygame.quit()
    pa.stop()
    pb.stop()
    GPIO.cleanup()