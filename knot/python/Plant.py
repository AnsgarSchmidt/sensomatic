import mraa
import time

pump = mraa.Pwm(3)
pump.period_us(1000)
pump.enable(True)

pump.write(0.0)

#pump.write(1.0)
#time.sleep(0.4)
#pump.write(0.4)
#time.sleep(1)
#pump.write(0.5)
#time.sleep(1)
#pump.write(0.4)
#time.sleep(1)  
#pump.write(0.0)

led = mraa.Pwm(5)
led.period_us(700)
led.enable(True)

for i in range(100):
	t = i / 100.0
	print t
	led.write(t)
	time.sleep(1)

led.write(0.0)
