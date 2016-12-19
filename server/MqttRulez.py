import os
import time
import redis
import Queue
import random
import datetime
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   Tts                import Tts
from   Room               import Room
from   Template           import TemplateMatcher
from   Mpd                import Mpd
from   Chromecast         import Chromecast
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

    def _process(self):

        k, v = self._workingQueue.get()

        keys = k.split("/")

        if keys[0] == Room.BATH_ROOM:

            if keys[1] == "button":
                print "button"

                #Ansi shower
                if v == "1":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._mqclient.publish("bathroom/light/rgb","0,0,0")
                        Mpd().getServerbyName("Bath").stop()
                        self._redis.delete("shower")
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Ansi'), Room.BATH_ROOM)
                    else:
                        print "Start shower"
                        self._mqclient.publish("bathroom/light/rgb","255,255,255")
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Ansi'), Room.BATH_ROOM)
                        s = Mpd().getServerbyName("Bath")
                        s.stop()
                        s.emptyPlaylist()
                        if datetime.datetime.now().hour > 10:
                            print "Using Drei ???"
                            dflist = s.getPlaylists('Drei ???|Die drei ???')
                            if len(dflist) > 0:
                                print "found %d entries" % len(dflist)
                                s.loadPlaylist(random.choice(dflist))
                                s.randomize(0)
                            else:
                                print "Using Starred"
                                for i in s.getPlaylists('Starred'):
                                    s.loadPlaylist(i)
                                s.randomize(1)
                        else:
                            print "Using Inforadio"
                            s.add("http://inforadio.de/livemp3")
                        s.volume(60)
                        s.play()

                # Ansi bath
                if v == "2":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._redis.delete("bath")
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Ansi'), Room.BATH_ROOM)
                        self._mqclient.publish("ansiroom/settemp", "boost")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        print "Start bath"
                        self._mqclient.publish("bathroom/light/rgb", "255,42,23")
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Ansi'), Room.BATH_ROOM)
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        s = Mpd().getServerbyName("Bath")
                        s.emptyPlaylist()
                        for i in s.getPlaylists('Starred'):
                            s.loadPlaylist(i)
                        s.randomize(1)
                        s.volume(15)
                        s.play()

                # Ansi nix
                if v == "3":
                    print "Switching off everyting in the bathroom"
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    self._tts.createWavFile(self._template.getAcknowledgeDeactivateBath('Ansi'), Room.BATH_ROOM)
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    Mpd().getServerbyName("Bath").stop()

                #Tiffy shower
                if v == "4":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._mqclient.publish("bathroom/light/rgb","0,0,0")
                        self._redis.delete("shower")
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Phawx'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Phawx'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._mqclient.publish("bathroom/light/rgb","255,255,255")
                        Mpd().getServerbyName("Bath").stop()

                #Tiffy bath
                if v == "5":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._redis.delete("bath")
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Phawx'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        print "Start bath"
                        self._mqclient.publish("bathroom/light/rgb","0,25,255")
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Phawx'), Room.BATH_ROOM)
                        b = Mpd().getServerbyName("Bath")
                        b.stop()
                        b.emptyPlaylist()
                        b.add("file:///mnt/tts/naturesounds.ogg")
                        b.play()

                # Tiffy nix
                if v == "6":
                    print "Switching off everyting in the bathroom"
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    #self._tts.createWavFile(self._template.getAcknowledgeDeactivateBath('Phawx'), Room.BATH_ROOM)
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    b = Mpd().getServerbyName("Bath").stop()

                # Guest shower
                if v == "7":
                    if self._redis.exists("shower"):
                        print "Stop shower"
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._redis.delete("shower")
                        self._tts.createWavFile(self._template.getAcknowledgeEndShower('Guest'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        print "Start shower"
                        self._tts.createWavFile(self._template.getAcknowledgeStartShower('Guest'), Room.BATH_ROOM)
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._mqclient.publish("bathroom/light/rgb", "255,255,255")
                        s = Mpd().getServerbyName("Bath")
                        s.emptyPlaylist()
                        for i in s.getPlaylists('Starred'):
                            s.loadPlaylist(i)
                        s.randomize(1)
                        s.volume(62)
                        s.play()

                # Guest bath
                if v == "8":
                    if self._redis.exists("bath"):
                        print "Stop bath"
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._redis.delete("bath")
                        self._tts.createWavFile(self._template.getAcknowledgeEndBath('Guest'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        print "Start bath"
                        self._mqclient.publish("bathroom/light/rgb", "0,25,255")
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._tts.createWavFile(self._template.getAcknowledgeStartBath('Guest'), Room.BATH_ROOM)
                        Mpd().getServerbyName("Bath").stop()

                # Guest nix
                if v == "9":
                    print "Switching off everyting in the bathroom"
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    self._tts.createWavFile(self._template.getAcknowledgeDeactivateBath('Guest'), Room.BATH_ROOM)
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    Mpd().getServerbyName("Bath").stop()

            if keys[1] == "motion":
                print "motion in bath detected"
                self._redis.setex(Room.BATH_ROOM+"/populated", 60 * 60, time.time())
                if not self._redis.exists("PlayRadioInBath") and not self._redis.exists("shower") and not self._redis.exists("bath"):
                    print "Play Radio in Bath"
                    self._redis.setex("PlayRadioInBath", 60 * 60 * 2, time.time())
                    s = Mpd().getServerbyName("Bath")
                    s.stop()
                    s.emptyPlaylist()
                    s.add("http://inforadio.de/livemp3")
                    if datetime.datetime.now().hour in (1, 2, 3, 4, 5, 6, 7):
                        self._mqclient.publish("bathroom/light/rgb", "255,25,0")
                        s.volume(1)
                    if datetime.datetime.now().hour in (8,9):
                        self._mqclient.publish("bathroom/light/rgb", "255,255,255")
                        s.volume(42)
                    if datetime.datetime.now().hour in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20):
                        self._mqclient.publish("bathroom/light/rgb", "255,255,255")
                        s.volume(62)
                    if datetime.datetime.now().hour in (21, 22, 23, 0):
                        self._mqclient.publish("bathroom/light/rgb", "255,255,0")
                        s.volume(32)
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

            if keys[1] == "button":
                print "button"

                #Breakfast
                if v == "1":
                    print "Breakfast"

                # Lunch
                if v == "2":
                    print "Lunch"

                # Dinner
                if v == "3":
                    print "Dinner"

            if keys[1] == "motion":
                print "motion in livingroom detected"
                self._redis.setex(Room.LIVING_ROOM+"/populated", 60 * 60, time.time())

            if keys[1] == "tank":

                if keys[2] == "humidity":
                    self._mqclient.publish("livingroom/humidity", v)

                if keys[2] == "airtemp":
                    self._mqclient.publish("livingroom/temperature", v)

                if keys[2] == "waterlevel":
                    fval = float(v)
                    if self._lastwaterlevel != fval:
                        if fval > 0.5:
                            print "Waterlevel back to normal"
                            self._tts.createWavFile(self._template.getWaterlevelNormal(), Room.LIVING_ROOM)
                        else:
                            print "Waterlevel is to low now"
                            self._tts.createWavFile(self._template.getWaterlevelLow(), Room.LIVING_ROOM)
                        self._lastwaterlevel = fval

        if keys[0] == Room.ANSI_ROOM:

            if keys[1] == "button":
                print "button"

                #Ansi Read
                if v == "1":
                    print "Activating Reading in AnsiRoom"
                    if self._redis.exists("AnsiRoomFallingAsleep"):
                        self._redis.delete("AnsiRoomFallingAsleep")

                    self._redis.setex("AnsiRoomReading", 60 * 60 * 1, time.time())

                # Ansi Sleep
                if v == "2":
                    print "Activating Sleeping Sequence in AnsiRoom"

                    if self._redis.exists("AnsiRoomReading"):
                        self._redis.delete("AnsiRoomReading")

                    self._redis.setex("AnsiRoomFallingAsleep", 60 * 60 * 5, time.time()) # Will be removed automatically
                    self._mqclient.publish("ansiroom/settemp", "10")

            if keys[1] == "motion":
                print "motion in ansi room detected"
                self._redis.setex(Room.ANSI_ROOM+"/populated", 60 * 60, time.time())
                if self._redis.exists("ansiwakeup"):
                    print "Ansiwakeup detected motion"
                    self._redis.delete("ansiwakeup")
                    self._mqclient.publish("ansiroom/settemp",                "boost" )
                    self._mqclient.publish("ansiroom/bedlight/sleep/sunrise", 0       )
                    self._mqclient.publish("corridor/light/main",             "TOGGLE")
                    self._mqclient.publish("ansiroom/light/main",             "TOGGLE")
                    self._tts.createWavFile(self._template.getWakeupText("Ansi"), Room.BATH_ROOM)
                    try:
                       Chromecast().playMusicURL('Chromeansi', 'http://rbb-mp3-fritz-m.akacast.akamaistream.net/7/799/292093/v1/gnl.akacast.akamaistream.net/rbb_mp3_fritz_m')
                    except:
                        pass

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
        self._mqclient       = mqtt.Client("MqttRulez", clean_session=True)
        self._redis          = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._tts            = Tts()
        self._template       = TemplateMatcher()
        self._info           = InformationFetcher()
        self._workingQueue   = Queue.Queue()
        self._lastwaterlevel = -1

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Rulez with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

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
    print "Start"

    m = MqttRulez()
    m.start()

    time.sleep(10)

    print "End"