import os
import redis
import threading
import ConfigParser
import paho.mqtt.client as mqtt
import time
import random
import datetime
from Tts import Tts
from Room import Room
from Template import TemplateMatcher
from Mpd import Mpd

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

        if keys[0] == Room.BATH_ROOM:

            if keys[1] == "temp":
                print "temp"

            if keys[1] == "button":
                print "button"

                #Wasching machine
                if v == "1":
                    if self._redis.exists("Waschingmachine"):
                        print "Ack empty wasching machine"
                        self._redis.delete("Waschingmachine")
                        self._tts.createWavFile(self._template.getAcknowledgeEndWashingMachine(), Room.BATH_ROOM)
                    else:
                        print "Ack start wasching machine"
                        self._redis.setex("Waschingmachine", 60 * 60 * 24 * 1, time.time())
                        self._tts.createWavFile(self._template.getAcknowledgeStartWashingMachine(), Room.BATH_ROOM)

                #Ansi shower
                if v == "2":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Ansi'), Room.BATH_ROOM)
                        self._redis.delete("shower")
                        Mpd().getServerbyName("Bath").stop()
                        self._mqclient.publish("bathroom/light/rgb/r","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","0")

                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Ansi'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        s = Mpd().getServerbyName("Bath")
                        s.emptyPlaylist()
                        if datetime.datetime.now().hour > 11:
                            dflist = s.getPlaylists('Drei ???|Die drei ??? \xe2\x80\x93')
                            if len(dflist) > 0:
                                s.loadPlaylist(random.choice(dflist))
                            else:
                                for i in s.getPlaylists('Starred'):
                                    s.loadPlaylist(i)
                            s.randomize(0)
                        else:
                            for i in s.getPlaylists('Starred'):
                                s.loadPlaylist(i)
                            s.randomize(1)
                        s.volume(90)
                        s.play()
                        self._mqclient.publish("bathroom/light/rgb/r","255")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","255")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","255")

                #Tiffy shower
                if v == "3":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Phawx'), Room.BATH_ROOM)
                        self._redis.delete("shower")
                        self._mqclient.publish("bathroom/light/rgb/r","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","0")
                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Phawx'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        self._mqclient.publish("bathroom/light/rgb/r","255")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","255")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","255")

                #Ansi bath
                if v == "4":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Ansi'), Room.BATH_ROOM)
                        self._redis.delete("bath")
                        Mpd().getServerbyName("Bath").stop()
                        self._mqclient.publish("bathroom/light/rgb/r","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","0")
                    else:
                        print "Start bath"
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Ansi'), Room.BATH_ROOM)
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        s = Mpd().getServerbyName("Bath")
                        s.emptyPlaylist()
                        for i in s.getPlaylists('Starred'):
                            s.loadPlaylist(i)
                        s.randomize(1)
                        s.volume(15)
                        s.play()
                        self._mqclient.publish("bathroom/light/rgb/r","255")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","42")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","23")

                #Tiffy bath
                if v == "5":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Phawx'), Room.BATH_ROOM)
                        self._redis.delete("bath")
                        self._mqclient.publish("bathroom/light/rgb/r","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","0")
                    else:
                        print "Start bath"
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Phawx'), Room.BATH_ROOM)
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        self._mqclient.publish("bathroom/light/rgb/r","0")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/g","25")
                        time.sleep(1)
                        self._mqclient.publish("bathroom/light/rgb/b","255")

            if keys[1] == "motion":
                print "motion in bath detected"
                self._redis.setex(Room.BATH_ROOM+"/populated", 60 * 60, time.time())

        if keys[0] == Room.LIVING_ROOM:

            if keys[1] == "motion":
                print "motion in livingroom detected"
                self._redis.setex(Room.LIVING_ROOM+"/populated", 60 * 60, time.time())

        if keys[0] == Room.ANSI_ROOM:

            if keys[1] == "motion":
                print "motion in ansi room detected"
                self._redis.setex(Room.ANSI_ROOM+"/populated", 60 * 60, time.time())

        if keys[0] == Room.TIFFY_ROOM:

            if keys[1] == "motion":
                print "motion in tiffy room detected"
                self._redis.setex(Room.TIFFY_ROOM+"/populated", 60 * 60, time.time())

    def __init__(self):
        random.seed
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

        self._mqclient = mqtt.Client("MqttRulez", clean_session=True)
        self._redis    = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._tts      = Tts()
        self._template = TemplateMatcher()

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