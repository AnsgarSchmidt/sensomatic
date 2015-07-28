import mraa
import time

led = mraa.Gpio(4)
led.dir(mraa.DIR_OUT)

for i in range(10):
    led.write(1)
    time.sleep(1)
    led.write(0)
    time.sleep(1)
