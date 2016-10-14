import os
import redis
import time
import datetime
import colorsys
import threading
import ConfigParser
import paho.mqtt.client as mqtt
from Room import Room
from InformationFetcher import InformationFetcher

class LightController(threading.Thread):

    def __init__(self):
        self._info = InformationFetcher()
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient = mqtt.Client("LightController", clean_session=True)
        self._redis = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"),
                                        port=self._config.get("REDIS", "ServerPort"), db=0)

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected with result code %s" % rc
        #self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect LightController"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        time.sleep(1)
        while True:
            self._mqclient.loop(max_packets=100)
            self.ansiRoom()
            self._mqclient.loop(max_packets=100)
            time.sleep(60)

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

        if not self._config.has_section('REDIS'):
            print "Adding Redis part"
            update = True
            self._config.add_section("REDIS")

        if not self._config.has_option("REDIS", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("REDIS", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("REDIS", "ServerPort"):
            print "No Server Port"
            update = True
            self._config.set("REDIS", "ServerPort", "6379")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def fill(self, size, val):
        values = ""
        for i in range(size):
            values += ",%d,%d,%d" % (val[0],val[1],val[2])
        return values[1:]

    def fillgradient(self, len):
        values = ""
        for i in range(len):
            values += ",%d,%d,%d" % (0,0,0)
        return values[1:]

    def setWorkingLight(self, val):
        self._mqclient.publish("ansiroom/bedlight/overhead/colour", self.fill(20, [val[0], val[1], val[2]]))
        self._mqclient.publish("ansiroom/bedlight/center/colour",   self.fill(20, [val[0], val[1], val[2]]))
        self._mqclient.publish("ansiroom/bedlight/left/colour",     self.fill(6,  [val[0], val[1], val[2]]))
        self._mqclient.publish("ansiroom/bedlight/right/colour",    self.fill(6,  [val[0], val[1], val[2]]))

    def ansiRoom(self):

        if self._info.isSomeoneInTheRoom(Room.ANSI_ROOM):

            lightlevel = self._info.getOutsideLightLevel()

            if lightlevel < 29.999:
                now  = datetime.datetime.now()
                blue = 1.0
                r    = 255
                g    = 255
                b    = 255

                if now.hour in (21, 22, 23):
                    m  = now.hour - 21
                    m *= 60
                    m += now.minute
                    max = 3 * 60
                    blue = float(m) / max
                    blue = 1 - blue

                if now.hour in (0, 1, 2, 3, 4, 5):
                    blue = 0.0

                if lightlevel > 0:
                    d = (30.0 - lightlevel) / 30.0
                    r *= d
                    g *= d
                    b *= d

                b *= blue
                self.setWorkingLight([int(r), int(g), int(b)])
            else:
                self.setWorkingLight([0, 0, 0])
        else:
            self.setWorkingLight([0, 0, 0])

if __name__ == "__main__":
    print "LightController test"

    l = LightController()
    l.start()
    time.sleep(23)


#_,_,_,weather,_,_,_ = InformationFetcher().getOutdoor()
