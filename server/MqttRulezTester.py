import os
import sys
import math
import time
import json
import redis
import Queue
import random
import datetime
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   Room               import Room
from   Template           import TemplateMatcher
from   Mpd                import Mpd
from   InformationFetcher import InformationFetcher


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
                sys.exit(1)

    def _process(self):

        k, v = self._workingQueue.get()

        keys = k.split("/")
        ########## dev code here
        ########## dev code here

    def __init__(self):
        random.seed
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir              = os.path.expanduser("~/.sensomatic")
        self._configFileName       = self._homeDir + '/config.ini'
        self._config               = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient             = mqtt.Client("MqttRulezTester", clean_session=True)
        self._redis                = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._template             = TemplateMatcher()
        self._info                 = InformationFetcher()
        self._workingQueue         = Queue.Queue()
        self._lastwaterlevel       = -1
        self._cortex_wan_rx        = 0
        self._cortex_wan_tx        = 0
        self._cortex_cortex_rx     = 0
        self._cortex_cortex_tx     = 0
        self._cortex_phawxansi_rx  = 0
        self._cortex_phawxansi_tx  = 0
        self._bike_laststep        = 0
        self._bike_starttime       = 0

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Rulez with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        while True:
            try:
                self._process()
            except Exception as e:
                print e

if __name__ == '__main__':
    print "Start"

    m = MqttRulez()
    m.start()

    time.sleep(42)

    print "End"
