import Queue
import serial
import time
import paho.mqtt.client as mqtt
import threading

__author__ = 'ansi'

sendQueue    = Queue.Queue()

class ReceiveThread(threading.Thread):
    """Threaded serial receive"""

    def __init__(self, ser, mqclient):
        threading.Thread.__init__(self)
        self._ser      = ser
        self._mqclient = mqclient

    def run(self):
        while True:
            line = self._ser.readline()
            element = line.split(',')
            command = int(element[0])
            if (command == 0):
                #print "Ack Comment"
                pass
            if (command == 1):
                print "Error:%s" % line
            if (command == 2):
                print "Set GRB"
            if (command == 3):
                print "Set R"
            if (command == 4):
                print "Set G"
            if (command == 5):
                print "Set B"
            if (command == 6):
                print "GetTemp"
            if (command == 7):
                print "GetHumidity"
            if (command == 8):
                print "GetLight"
            if (command == 9):
                temp = float(element[1].split(";")[0])
                #print "Temp:%f" % temp
                self._mqclient.publish("badezimmer/temperature", temp)
            if (command == 10):
                hum = float(element[1].split(";")[0])
                #print "Humidity:%f"  % hum
                self._mqclient.publish("badezimmer/humidity", hum)
            if (command == 11):
                light = float(element[1].split(";")[0])
                #print "Light:%d"  % light
                self._mqclient.publish("badezimmer/light", light)
            if (command == 12):
                button = int(element[1].split(";")[0])
                #print "Button Pressed:%d" % button
                self._mqclient.publish("badezimmer/button", button)

class SendThread(threading.Thread):
    """Threaded serial send"""

    def __init__(self, queue, ser):
        threading.Thread.__init__(self)
        self._queue = queue
        self._ser   = ser

    def run(self):
        while True:
            line = self._queue.get()
            self._ser.write(line + "\n")
            self._queue.task_done()
            time.sleep(0.1)

class TasksThread(threading.Thread):
    """Threaded measurement"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._queue = queue

    def run(self):
        while True:
            time.sleep(5)
            self._queue.put("6;") # Temperature
            self._queue.put("7;") # Humidity
            self._queue.put("8;") # Light

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("badezimmer/light/+")

def on_message(client, userdata, msg):
    print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
    parts   = msg.topic.split("/")
    channel = parts[2]
    val     = int(msg.payload)
    if channel == "r":
        sendQueue.put("3,%d;" % val)
    if channel == "g":
        sendQueue.put("4,%d;" % val)
    if channel == "b":
        sendQueue.put("5,%d;" % val)

if __name__ == "__main__":
    print "Start"

    ser = serial.Serial("/dev/ttyUSB0", 115200)

    mqclient = mqtt.Client("badezimmer", clean_session=True)
    mqclient.connect("ansinas", 1883, 60)
    mqclient.on_connect = on_connect
    mqclient.on_message = on_message

    receive = ReceiveThread(ser, mqclient)
    receive.setDaemon(True)
    receive.start()

    send = SendThread(sendQueue, ser)
    send.setDaemon(True)
    send.start()

    tasks = TasksThread(sendQueue)
    tasks.setDaemon(True)
    tasks.start()

    for i in range(222):
        sendQueue.put("3,%d;" % i)
        sendQueue.put("4,%d;" % i)
        sendQueue.put("5,%d;" % i)

    mqclient.loop_forever()