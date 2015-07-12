import os
import ConfigParser
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import threading

class Light(threading.Thread):

    LIVING_ROOM  = 23
    HACKING_ROOM = 24
    ANSI_ROOM    = 25
    TIFFY_ROOM   = 16
    KITCHEN      = 20
    CORRIDOR     = 21
    STORAGE      = 13
    ENTRANCE     = 19
    BATHROOM     = 26

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

        if not self._config.has_section('LIGHT'):
            print "Adding Redis part"
            update = True
            self._config.add_section("LIGHT")

        if not self._config.has_option("LIGHT", "Active"):
            print "Active"
            update = True
            self._config.set("LIGHT", "Active", "False")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def _initGPIO(self):
        self._status = dict()
	GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._gpios = {Light.LIVING_ROOM, Light.HACKING_ROOM, Light.ANSI_ROOM, Light.TIFFY_ROOM , Light.KITCHEN, Light.CORRIDOR, Light.STORAGE, Light.ENTRANCE, Light.BATHROOM}
        for i in self._gpios:
            GPIO.setup(i, GPIO.OUT)
	    self._status[i] = False

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

        if self._config.getboolean("LIGHT","Active"):
	    print "Light active"
            self._initGPIO()
            self._mqclient = mqtt.Client("light", clean_session=True)
            self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
            self._mqclient.on_connect = self._on_connect
            self._mqclient.on_message = self._on_message
            self._mqclient.on_disconnect = self._on_disconnect
            self._mqclient.loop_forever()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected with result code %s" % rc
        self._mqclient.subscribe("+/light/main")

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
	s = msg.topic.split("/")
	if s[1] == 'light' and s[2] == 'main':
		if s[0] == 'livingroom':
			self._switch(Light.LIVING_ROOM, msg.payload)
                if s[0] == 'hackingroom':
                        self._switch(Light.HACKING_ROOM, msg.payload)
                if s[0] == 'ansiroom':
                        self._switch(Light.ANSI_ROOM, msg.payload)
                if s[0] == 'tiffyroom':
                        self._switch(Light.TIFFY_ROOM, msg.payload)
                if s[0] == 'kitchen':
                        self._switch(Light.KITCHEN, msg.payload)
                if s[0] == 'corridor':
                        self._switch(Light.CORRIDOR, msg.payload)
                if s[0] == 'storage':
                        self._switch(Light.STORAGE, msg.payload)
                if s[0] == 'entrance':
                        self._switch(Light.ENTRANCE, msg.payload)
                if s[0] == 'bathroom':
                        self._switch(Light.BATHROOM, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect"

    def _toggle(self, room):
	GPIO.output(room, True)
	time.sleep(0.1)
	GPIO.output(room, False)

    def _switch(self, room, status):
	if status == "ON" and not self._status[room]:
		self._toggle(room)
		if room == Light.LIVING_ROOM:
                        time.sleep(0.1)
                        self._toggle(room)
		self._status[room] = True
	if status == "OFF" and self._status[room]:
		self._toggle(room)
                if room == Light.LIVING_ROOM:
                        time.sleep(0.1)
                        self._toggle(room)
		self._status[room] = False 
	if status == "TOGGLE":
		self._toggle(room)
                if room == Light.LIVING_ROOM:
                        time.sleep(0.1)
                        self._toggle(room)

if __name__ == "__main__":

    print "Test"
    l = Light()
    time.sleep(100)

