import serial
import time
import paho.mqtt.client as mqtt


__author__ = 'ansi'

class Sensomatik:

    def __init__(self):
        self._com = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)

    def setRGB(self, r, g, b):
        print "Setting"
        self._com.flushInput()
        self._com.write("3,%d;" % (r)) # rgb
        print self._com.readline()
        self._com.write("4,%d;" % (g)) # rgb
        print self._com.readline()
        self._com.write("5,%d;" % (b)) # rgb
        print self._com.readline()

    def getTemp(self):
        self._com.flushInput()
        self._com.write("6;")
        print self._com.readline()

    def getHum(self):
        self._com.flushInput()
        self._com.write("7;")
        print self._com.readline()

    def setR(self,r):
        self._com.flushInput()
        self._com.write("3,%d;" % r)
        print self._com.readline()

    def close(self):
        self._com.close()


if __name__ == "__main__":
    print "Start"

    client            = mqtt.Client("badezimmer", clean_session=True)

    client.connect("ansinas", 1883, 60)

    sens = Sensomatik()
    for z in range(1):
            sens.setRGB(0,0,0)
            sens.setRGB(255,0,0)
            sens.setRGB(0,255,0)
            sens.setRGB(0,0,255)
            sens.setRGB(0,255,0)
            sens.setRGB(255,255,255)
            sens.setRGB(0,0,0)

    sens.getTemp()
    sens.getHum()

    sens.close()
