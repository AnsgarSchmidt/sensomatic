import Queue
import threading
import time
import struct
import serial
import colorsys
import paho.mqtt.client as mqtt

DEVICES = {
    "OVERHEAD":        0,
    "SLEEP":           1,
    "BED_LEFT":        2,
    "BED_CENTER":      3,
    "BED_RIGHT":       4
}

NUM_LEDS = {
    "OVERHEAD":         20,
    "SLEEP":           144,
    "BED_LEFT":         18,
    "BED_CENTER":       14,
    "BED_RIGHT":        18
}

ColorTemperature = {
  "Candle":                   [0xFF, 0x93, 0x29],
  "Tungsten40W":              [0xFF, 0xC5, 0x8F],
  "Tungsten100W":             [0xFF, 0xD6, 0xAA],
  "Halogen":                  [0xFF, 0xF1, 0xE0],
  "CarbonArc":                [0xFF, 0xFA, 0xF4],
  "HighNoonSun":              [0xFF, 0xFF, 0xFB],
  "DirectSunlight":           [0xFF, 0xFF, 0xFF],
  "OvercastSky":              [0xC9, 0xE2, 0xFF],
  "ClearBlueSky":             [0x40, 0x9C, 0xFF],
  "WarmFluorescent":          [0xFF, 0xF4, 0xE5],
  "StandardFluorescent":      [0xF4, 0xFF, 0xFA],
  "CoolWhiteFluorescent":     [0xD4, 0xEB, 0xFF],
  "FullSpectrumFluorescent":  [0xFF, 0xF4, 0xF2],
  "GrowLightFluorescent":     [0xFF, 0xEF, 0xF7],
  "BlackLightFluorescent":    [0xA7, 0x00, 0xFF],
  "MercuryVapor":             [0xD8, 0xF7, 0xFF],
  "SodiumVapor":              [0xFF, 0xD1, 0xB2],
  "MetalHalide":              [0xF2, 0xFC, 0xFF],
  "HighPressureSodium":       [0xFF, 0xB7, 0x4C],
  "UncorrectedTemperature":   [0xFF, 0xFF, 0xFF]
}

sendQueue    = Queue.Queue()

class ReceiveThread(threading.Thread):

    def __init__(self, ser, mqclient):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._ser      = ser
        self._mqclient = mqclient

    def run(self):
        while True:
            line = self._ser.readline().strip()
            self._mqclient.publish("ansiroom/bed/plant", line)

class SendThread(threading.Thread):

    def __init__(self, queue, ser):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._queue = queue
        self._ser   = ser

    def run(self):
        while True:
            s = self._queue.get()
            #print ":".join("{:02x}".format(ord(c)) for c in s)
            for i in s:
                self._ser.write(i)
                self._ser.flush()
                time.sleep(0.05)
            self._queue.task_done()
            #print "DONE"
            time.sleep(0.5)

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("ansiroom/bedlight/#")

def on_message(client, userdata, msg):
    print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
    parts   = msg.topic.split("/")
    device  = parts[2]
    command = parts[3]
    val     = msg.payload
    print " Device: %s  Command %s  Value %s" % ( device, command, val )

    if command == "fire":
        if device == "sleep":
            Fire(DEVICES['SLEEP'], int(val))
        if device == "center":
            Fire(DEVICES['BED_CENTER'], int(val))

    if command == "sunrise":
        if device == "sleep":
            Sunrise(DEVICES['SLEEP'], 1, int(val))

    if command == "colour":
        values = val.split(",")
        c = []
        for i in range(0, len(values), 3):
            a = []
            a.append(int(values[i+0]))
            a.append(int(values[i+1]))
            a.append(int(values[i+2]))
            c.append(a)
        if device == "sleep":
            RGB(DEVICES['SLEEP'], c)
        if device == "overhead":
            RGB(DEVICES['OVERHEAD'], c)
        if device == "center":
            RGB(DEVICES['BED_CENTER'], c)
        if device == "left":
            RGB(DEVICES['BED_LEFT'], c)
        if device == "right":
            RGB(DEVICES['BED_RIGHT'], c)

def RGB(device, values):

    if device > 4 or device < 0:
        return
    s = ''
    s += struct.pack("!BB", 0, device)
    for i in values:
        s += struct.pack('!{0}B'.format(len(i)), *i)
    s += ";"
    sendQueue.put(s)

def HSV(device, values):

    if device > 4 or device < 0:
        return

    s = ''
    s += struct.pack("!BB", 1, device)

    for i in values:
        s += struct.pack('!{0}B'.format(len(i)), *i)

    s += ";"
    sendQueue.put(s)

def fill(size, val):
    values = []

    for i in range(size):
        values.append(val)

    return values

def Fire(device, intensity):

    if intensity < 1:
        s = struct.pack('!BBB', 2, device, 0)
        s += ";"
        sendQueue.put(s)
        RGB(device, fill(20, [0, 0, 0]))
    else:
        s = struct.pack('!BBB', 2, device, intensity)
        s += ";"
        sendQueue.put(s)

def Sunrise(device, num, percentage):

    if device > 2 or device < 0:
        return

    if percentage < 0:
        RGB(device, fill(num, [0, 0, 0]))
        return

    if percentage > 99:
        RGB(device, fill(num, [255, 255, 255]))

    else:
        h =         ( (250.0 +  (85.0 / 100.0) * percentage)        % 256   )
        s = 255.0 - (  (51.0 / 2000.0)         * (percentage * percentage)  )
        v =         ( (255.0 /  100.0)         * percentage                 )
        a, b, c = colorsys.hsv_to_rgb( (h / 255.0), (s / 255.0), (v / 255.0) )
        RGB(device, fill(num, [int(a * 255),int(b * 255),int(c * 255)]))

if __name__ == "__main__":

    ser = serial.Serial("/dev/ttyUSB0", 9600)

    mqclient            = mqtt.Client("ansibed", clean_session=True)
    mqclient.on_connect = on_connect
    mqclient.on_message = on_message
    mqclient.connect("cortex", 1883, 60)

    receive = ReceiveThread(ser, mqclient)
    receive.start()

    send = SendThread(sendQueue, ser)
    send.start()

    Fire(DEVICES['SLEEP'], 0)
    Fire(DEVICES['BED_CENTER'], 0)

    RGB(DEVICES['OVERHEAD'],   [[0,0,0]])
    RGB(DEVICES['SLEEP'],      [[0,0,0]])
    RGB(DEVICES['BED_LEFT'],   [[0,0,0]])
    RGB(DEVICES['BED_CENTER'], [[0,0,0]])
    RGB(DEVICES['BED_RIGHT'],  [[0,0,0]])

    mqclient.loop_forever()
