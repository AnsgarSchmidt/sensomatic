import time
import TM1638

DIO = 17
CLK = 27
STB = 22

display = TM1638.TM1638(DIO, CLK, STB)

for i in range(7):
    display.enable(i)
    display.set_text("88888888")
    time.sleep(1)

display.enable(0)

for i in range(8):
    display.set_led(i, 1)
    display.set_segment(i, i)
    time.sleep(0.1)

for i in range(8):
    display.set_led(i, 0)
    display.set_segment(i, 0)
    time.sleep(0.1)

for i in range(1078):
    display.set_text("%08d"%i)

time.sleep(6)
display.disable()