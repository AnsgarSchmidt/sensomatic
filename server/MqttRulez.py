import os
import redis
import threading
import ConfigParser
import paho.mqtt.client as mqtt
import time
import random
import datetime
from Tts                import Tts
from Room               import Room
from Template           import TemplateMatcher
from Mpd                import Mpd
from Chromecast         import Chromecast
from InformationFetcher import  InformationFetcher

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

            if keys[1] == "button":
                print "button"

                #Ansi shower
                if v == "1":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._redis.delete("shower")
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Ansi'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                        self._mqclient.publish("bathroom/light/rgb","0,0,0")
                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Ansi'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        s = Mpd().getServerbyName("Bath")
                        s.emptyPlaylist()
                        s.add("http://inforadio.de/livemp3")
                        #if datetime.datetime.now().hour > 11:
                        #    dflist = s.getPlaylists('Drei ???|Die drei ??? \xe2\x80\x93')
                        #    if len(dflist) > 0:
                        #        s.loadPlaylist(random.choice(dflist))
                        #    else:
                        #        for i in s.getPlaylists('Starred'):
                        #            s.loadPlaylist(i)
                        #    s.randomize(0)
                        #else:
                        #    for i in s.getPlaylists('Starred'):
                        #        s.loadPlaylist(i)
                        #    s.randomize(1)
                        s.volume(60)
                        s.play()
                        self._mqclient.publish("bathroom/light/rgb","255,255,255")

                #Tiffy shower
                if v == "4":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._redis.delete("shower")
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Phawx'), Room.BATH_ROOM)
                        self._mqclient.publish("bathroom/light/rgb","0,0,0")
                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Phawx'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        self._mqclient.publish("bathroom/light/rgb","255,255,255")

                #Ansi bath
                if v == "2":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._redis.delete("bath")
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Ansi'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
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
                        self._mqclient.publish("bathroom/light/rgb","255,42,23")

                #Tiffy bath
                if v == "5":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Phawx'), Room.BATH_ROOM)
                        self._redis.delete("bath")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    else:
                        print "Start bath"
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Phawx'), Room.BATH_ROOM)
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        self._mqclient.publish("bathroom/light/rgb","0,25,255")

            if keys[1] == "motion":
                print "motion in bath detected"
                self._redis.setex(Room.BATH_ROOM+"/populated", 60 * 60, time.time())
                if not self._redis.exists("PlayRadioInBath") and not self._redis.exists("shower") and not self._redis.exists("bath"):
                    self._redis.setex("PlayRadioInBath", 60 * 60, time.time())
                    s = Mpd().getServerbyName("Bath")
                    s.emptyPlaylist()
                    s.add("http://inforadio.de/livemp3")
                    s.volume(42)
                    s.play()

            if keys[1] == "washingmachine":

                if keys[2] == "current":
                    current = float(v)

                    # OFF
                    if current < 0.02:
                        if self._redis.exists("WashingmachineActive"):
                            print "Ack washing machine ready"
                            self._redis.delete("WashingmachineActive")
                            self._redis.setex("WashingmachineReady", 60 * 60 * 24 * 1, time.time())
                            for room in Room.ANNOUNCE_ROOMS:
                                if self._info.isSomeoneInTheRoom(room):
                                    self._tts.createWavFile(self._template.getAcknowledgeEndWashingMachine(), room)

                    # STANDBY
                    if 0.02 <= current < 0.08:
                        if not self._redis.exists("WashingmachineActive"):
                            self._redis.setex("WashingmachineActive", 60 * 60 * 24 * 1, time.time())
                            self._tts.createWavFile(self._template.getAcknowledgeStartWashingMachine(), Room.BATH_ROOM)

                    # WASHING
                    if current >= 0.8:
                        pass

                if keys[2] == "state":
                    if int(v) == 0:
                        if self._redis.exists("WashingmachineReady"):
                            print "Ack emptying washing machine"
                            self._redis.delete("WashingmachineReady")
                            self._tts.createWavFile(self._template.getAcknowledgeEmtyingWashingMachine(), Room.BATH_ROOM)

        if keys[0] == Room.LIVING_ROOM:

            if keys[1] == "motion":
                print "motion in livingroom detected"
                self._redis.setex(Room.LIVING_ROOM+"/populated", 60 * 60, time.time())

        if keys[0] == Room.ANSI_ROOM:

            if keys[1] == "motion":
                print "motion in ansi room detected"
                self._redis.setex(Room.ANSI_ROOM+"/populated", 60 * 60, time.time())
                if self._redis.exists("ansiwakeup"):
                    print "Ansiwakeup detected motion"
                    self._redis.delete("ansiwakeup")
                    Chromecast().playMusicURL('Chromeansi', 'http://rbb-mp3-fritz-m.akacast.akamaistream.net/7/799/292093/v1/gnl.akacast.akamaistream.net/rbb_mp3_fritz_m')
                    self._tts.createWavFile(self._template.getWakeupText("Ansi"), Room.ANSI_ROOM)
                    self._mqclient.publish("ansiroom/bedlight/sleep/sunrise", 0       )
                    self._mqclient.publish("corridor/light/main",             "TOGGLE")
                    self._mqclient.publish("ansiroom/light/main",             "TOGGLE")

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
        self._info     = InformationFetcher()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Rulez with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._process(msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_forever()

if __name__ == '__main__':
    print "Start"

    m = MqttRulez()
    m.start()

    time.sleep(10)

    print "End"