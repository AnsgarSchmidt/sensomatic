import os
import time
import Queue
import socket
import threading
import ConfigParser
import paho.mqtt.client as mqtt

class Carbon(threading.Thread):

    PATTERN=[#ANSIROOM
             "ansiroom/temperature",
             "ansiroom/co2",
             "ansiroom/motion",
             "ansiroom/bed/plant",
             #ANSISERVER
             "ansiserver/cputemp",
             "ansiserver/cpuuserusage",
             "ansiserver/loadlevel",
             "ansiserver/ramfree",
             "ansiserver/diskused",
             #BATHROOM
             "bathroom/temperature",
             "bathroom/humidity",
             "bathroom/combustible",
             "bathroom/light",
             "bathroom/motion",
             #BATHSERVER
             "bathserver/cputemp",
             "bathserver/cpuuserusage",
             "bathserver/loadlevel",
             "bathserver/ramfree",
             "bathserver/diskused",
             #LIVINGROOM TANK
             "livingroom/tank/whitelight",
             "livingroom/tank/bluelight",
             "livingroom/tank/settemp",
             "livingroom/tank/watertemp",
             "livingroom/tank/airtemp",
             "livingroom/tank/humidity",
             "livingroom/tank/heater",
             "livingroom/tank/waterlevel",
             #KITCHEN
             "kitchen/water/airtemp",
             "kitchen/water/humidity",
             "kitchen/water/valve",
             #HAL
             "hal/cputemp",
             "hal/cpuuserusage",
             "hal/loadlevel",
             "hal/ramfree",
             "hal/diskused",
             #BATHROOM WASHINGMACHINE
             "bathroom/washingmachine/voltage",
             "bathroom/washingmachine/current",
             "bathroom/washingmachine/state",
             #WLAN PRESENTS
             "ansi/wlanPresents",
             "tiffy/wlanPresents",
             #CORTEX
             "cortex/wan/rx",
             "cortex/wan/tx",
             "cortex/cortex/rx",
             "cortex/cortex/tx",
             "cortex/phawxansi/rx",
             "cortex/phawxansi/tx",
             "cortex/wan/rxdelta",
             "cortex/wan/txdelta",
             "cortex/cortex/rxdelta",
             "cortex/cortex/txdelta",
             "cortex/phawxansi/rxdelta",
             "cortex/phawxansi/tdeltax",
             #POWERSERVER
             "powerserver/cputemp",
             "powerserver/cpuuserusage",
             "powerserver/loadlevel",
             "powerserver/ramfree",
             "powerserver/diskused",
    ]

    def _readConfig(self):
        update = False

        if not os.path.isdir(self._homeDir):
            print "Creating homeDir"
            os.makedirs(self._homeDir)

        if os.path.isfile(self._configFileName):
            self._config.read(self._configFileName)
        else:
            print "Config file not found"
            update = True

        if not self._config.has_section('CARBON'):
            print "Adding CARBON part"
            update = True
            self._config.add_section("CARBON")

        if not self._config.has_option("CARBON", "Address"):
            print "No Server Address"
            update = True
            self._config.set("CARBON", "Address", "<ServerAddress>")

        if not self._config.has_option("CARBON", "Port"):
            print "No Port"
            update = True
            self._config.set("CARBON", "Port", "2003")

        if not self._config.has_section('MQTT'):
            print "Adding MQTT part"
            update = True
            self._config.add_section("MQTT")

        if not self._config.has_option("MQTT", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("MQTT", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("MQTT", "ServerPort"):
            print "No Server Port"
            update = True
            self._config.set("MQTT", "ServerPort", "1883")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._connect()
        self._mqclient       = mqtt.Client("Carbon", clean_session=True)
        self._workingQueue   = Queue.Queue()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Carbon with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def _connect(self):
        try:
            self._socket = socket.socket()
            self._socket.connect((self._config.get("CARBON", "Address"), int(self._config.get("CARBON", "Port"))))
            print "Connected"
        except Exception as e:
            print "Error connecting to Carbin socket"
            print e

    def sendData(self, topic, value):
        try:
            message = '%s %s %d\n' % (topic, value, time.time())
            self._socket.sendall(message)
        except Exception as e:
            print "Error sending data"
            print e
            self._connect()

    def _process(self):
        k, v = self._workingQueue.get()

        if k in Carbon.PATTERN:
            a = k.replace("/", ".")
            self.sendData(a, v)
        else:
            pass
            #print k, v

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()

        while True:
            try:
                self._process()
            except:
                pass

if __name__ == '__main__':
    print "Test"
    c = Carbon()
    c.start()
    time.sleep(23)
