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


class Exercise(threading.Thread):

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

        if not self._config.has_section('EXERCISE'):
            print "Adding Exercise part"
            update = True
            self._config.add_section("EXERCISE")

        if not self._config.has_option("EXERCISE", "kmperweek"):
            print "No Server Address"
            update = True
            self._config.set("EXERCISE", "kmperweek", 100)

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit(1)

    def _getdistance(self, distance):
        now                  = datetime.datetime.now()
        monday               = now.replace(hour=0, minute=0, second=0, microsecond=0)
        monday               = monday - datetime.timedelta(days=now.weekday())
        minutes_since_monday = (now - monday).total_seconds() / 60.0
        should_distance      = self._meterPerMinute * minutes_since_monday
        diff_distance        = distance - should_distance
        return diff_distance

    def _process(self):

        k, v           = self._workingQueue.get()
        keys           = k.split("/")
        total_distance = 0

        if self._redis.exists("exercise-total-distance"):
            total_distance = float(self._redis.get("exercise-total-distance"))

        if keys[0] == "bike":

            if keys[1] == "distance":
                total_distance += float(v)

                if (time.time() - self._lastAnnounce) > (60 * 1):
                    diff_distance = self._getdistance(total_distance)
                    self._mqclient.publish("ansiroom/ttsout", self._template.getBikeStatus(total_distance / 1000.0, diff_distance / 1000.0))
                    self._lastAnnounce = time.time()

        self._redis.setex("exercise-total-distance", 60 * 60 * 24 * 3, total_distance)

    def __init__(self):
        random.seed
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir              = os.path.expanduser("~/.sensomatic")
        self._configFileName       = self._homeDir + '/config.ini'
        self._config               = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient             = mqtt.Client("Exercise", clean_session=True)
        self._redis                = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._template             = TemplateMatcher()
        self._info                 = InformationFetcher()
        self._workingQueue         = Queue.Queue()
        self._meterPerMinute       = (self._config.getfloat("EXERCISE", "kmperweek") / (7 * 24 * 60)) * 1000.0
        self._lastAnnounce         = time.time()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected Exercise with result code %s" % rc
        self._mqclient.subscribe("bike/#")

    def _on_message(self, client, userdata, msg):
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect Excercise"

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

    e = Exercise()
    e.start()

    time.sleep(42)

    print "End"
