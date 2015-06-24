import os
import redis
import threading
import ConfigParser
import paho.mqtt.client as mqtt
import time

class MqttRulez(threading.Thread):

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

    def _process(self, k, v):

        keys = k.split("/")

        if keys[0] == "bathroom":
            if keys[1] == "temp":
                print "temp"

            if keys[1] == "button":
                print "button"
                if v == "1":
                    print "Washing machine"
                    if self._redis.exists("Waschingmachine"):
                        print "Token exists so remove"
                        self._redis.delete("Waschingmachine")

                    else:
                        print "Token does not exists"
                        self._redis.setex("Waschingmachine", 60 * 60 * 24 * 2, time.time())




    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

        self._mqclient = mqtt.Client("MqttRulez", clean_session=True)
        self._redis    = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._process(msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect = self._on_connect
        self._mqclient.on_message = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_forever()

if __name__ == '__main__':
    print "Start"

    m = MqttRulez()
    m.start()

    time.sleep(10)

    print "End"