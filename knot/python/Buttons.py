import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

def testfunc(param):
        print "Pressed"
        print param

GPIO.add_event_detect(17, GPIO.RISING, callback=testfunc, bouncetime=300)

while True:
        time.sleep(1)

