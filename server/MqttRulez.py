import os
import sys
import time
import json
import redis
import Queue
import random
import logging
import datetime
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   Room               import Room
from   Template           import TemplateMatcher
from   Mpd                import Mpd
from   Chromecast         import Chromecast
from   InformationFetcher import InformationFetcher


class MqttRulez(threading.Thread):

    def _readConfig(self):
        update = False

        if not os.path.isdir(self._homeDir):
            self._logger.warn("Creating homeDir")
            os.makedirs(self._homeDir)

        if os.path.isfile(self._configFileName):
            self._config.read(self._configFileName)
        else:
            self._logger.warn("Config file not found")
            update = True

        if not self._config.has_section('MQTT'):
            self._logger.warn("Adding MQTT part")
            update = True
            self._config.add_section("MQTT")

        if not self._config.has_option("MQTT", "ServerAddress"):
            self._logger.warn("No Server Address")
            update = True
            self._config.set("MQTT", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("MQTT", "ServerPort"):
            self._logger.warn("No Server Port")
            update = True
            self._config.set("MQTT", "ServerPort", "1883")

        if not self._config.has_section('REDIS'):
            self._logger.warn("Adding Redis part")
            update = True
            self._config.add_section("REDIS")

        if not self._config.has_option("REDIS", "ServerAddress"):
            self._logger.warn("No Server Address")
            update = True
            self._config.set("REDIS", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("REDIS", "ServerPort"):
            self._logger.warn("No Server Port")
            update = True
            self._config.set("REDIS", "ServerPort", "6379")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit(1)

    def _process(self):

        k, v = self._workingQueue.get()

        keys = k.split("/")

        if keys[0] == Room.BATH_ROOM:

            if keys[1] == "button":
                self._logger.info("button")

                #Ansi shower
                if v == "1":
                    if self._redis.exists("shower"):
                        self._logger.info("Stop shower")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndShower('Ansi'))
                        Mpd().getServerbyName("Bath").stop()
                        self._redis.delete("shower")
                    else:
                        self._logger.info("Start shower")
                        self._mqclient.publish("bathroom/light/rgb", "255,255,255")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartShower('Ansi'))
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        s = Mpd().getServerbyName("Bath")
                        s.stop()
                        s.emptyPlaylist()
                        if datetime.datetime.now().hour > 10:
                            self._logger.info("Using Drei ???")
                            dflist = s.getPlaylists('Drei ???|Die drei ???')
                            if len(dflist) > 0:
                                self._logger.info("found %d entries" % len(dflist))
                                s.loadPlaylist(random.choice(dflist))
                                s.randomize(0)
                            else:
                                self._logger.warn("Can not dinf ??? using Starred instead")
                                for i in s.getPlaylists('Starred'):
                                    s.loadPlaylist(i)
                                s.randomize(1)
                        else:
                            self._logger.info("Using Inforadio")
                            s.add("http://inforadio.de/livemp3")
                        s.volume(60)
                        s.play()

                # Ansi bath
                if v == "2":
                    if self._redis.exists("bath"):
                        self._logger.info("Stop bath")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndBath('Ansi'))
                        self._redis.delete("bath")
                        self._mqclient.publish("ansiroom/settemp", "boost")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        self._logger.info("Start bath")
                        self._mqclient.publish("bathroom/light/rgb", "255,42,23")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartBath('Ansi'))
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
                    self._logger.info("Switching off everyting in the bathroom")
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeDeactivateBath('Ansi'))
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    Mpd().getServerbyName("Bath").stop()

                #Tiffy shower
                if v == "4":
                    if self._redis.exists("shower"):
                        self._logger.info("Stop shower")
                        self._mqclient.publish("bathroom/light/rgb","0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndShower('Phawx'))
                        self._redis.delete("shower")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        self._logger.info("Start shower")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartShower('Phawx'))
                        self._redis.setex("shower", 60 * 60 * 2, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        self._mqclient.publish("bathroom/light/rgb","255,255,255")
                        Mpd().getServerbyName("Bath").stop()

                #Tiffy bath
                if v == "5":
                    if self._redis.exists("bath"):
                        self._logger.info("Stop bath")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndBath('Phawx'))
                        self._redis.delete("bath")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        self._logger.info("Start bath")
                        self._mqclient.publish("bathroom/light/rgb","0,25,255")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartBath('Phawx'))
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        b = Mpd().getServerbyName("Bath")
                        b.stop()
                        b.emptyPlaylist()
                        b.add("/home/pi/naturesounds.ogg")
                        b.play()

                # Tiffy nix
                if v == "6":
                    self._logger.info("Switching off everyting in the bathroom")
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    #self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeDeactivateBath('Phawx'))
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    b = Mpd().getServerbyName("Bath").stop()

                # Guest shower
                if v == "7":
                    if self._redis.exists("shower"):
                        self._logger.info("Stop shower")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndShower('Guest'))
                        self._redis.delete("shower")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        self._logger.info("Start shower")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartShower('Guest'))
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
                        self._logger.info("Stop bath")
                        self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEndBath('Guest'))
                        self._redis.delete("bath")
                        Mpd().getServerbyName("Bath").stop()
                    else:
                        self._logger.info("Start bath")
                        self._mqclient.publish("bathroom/light/rgb", "0,25,255")
                        self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartBath('Guest'))
                        self._redis.setex("bath", 60 * 60 * 5, time.time())
                        if self._redis.exists("PlayRadioInBath"):
                            self._redis.delete("PlayRadioInBath")
                        Mpd().getServerbyName("Bath").stop()

                # Guest nix
                if v == "9":
                    self._logger.info("Switching off everyting in the bathroom")
                    self._mqclient.publish("bathroom/light/rgb", "0,0,0")
                    self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeDeactivateBath('Guest'))
                    if self._redis.exists("shower"):
                        self._redis.delete("shower")
                    if self._redis.exists("bath"):
                        self._redis.delete("bath")
                    Mpd().getServerbyName("Bath").stop()

            if keys[1] == "motion":
                self._logger.info("motion in bath detected")
                self._redis.setex(Room.BATH_ROOM+"/populated", 60 * 60, time.time())
                if not self._redis.exists("PlayRadioInBath") and not self._redis.exists("shower") and not self._redis.exists("bath"):
                    self._logger.info("Play Radio in Bath")
                    self._redis.setex("PlayRadioInBath", 60 * 60 * 2, time.time())
                    s = Mpd().getServerbyName("Bath")
                    s.stop()
                    s.emptyPlaylist()
                    s.add("http://hal/news/tagesschau.mp3")
                    s.add("http://inforadio.de/livemp3")
                    if datetime.datetime.now().hour in (1, 2, 3, 4, 5):
                        self._mqclient.publish("bathroom/light/rgb", "255,25,0")
                        s.volume(1)
                    if datetime.datetime.now().hour in (6, 7, 8, 9):
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
                            self._logger.info("Ack washing machine ready")
                            self._redis.delete("WashingmachineActive")
                            self._redis.setex("WashingmachineReady", 60 * 60 * 24 * 1, time.time())
                            self._mqclient.publish("telegram", "Washing maching ready")
                            for room in Room.ANNOUNCE_ROOMS:
                                if self._info.isSomeoneInTheRoom(room):
                                    self._mqclient.publish("%s/ttsout" % room, self._template.getAcknowledgeEndWashingMachine())

                    # STANDBY
                    if 0.02 <= current < 0.08:
                        if not self._redis.exists("WashingmachineActive"):
                            self._redis.setex("WashingmachineActive", 60 * 60 * 24 * 1, time.time())
                            self._mqclient.publish("telegram", "Washing maching started")
                            self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeStartWashingMachine())

                    # Still WASHING
                    if current >= 0.8:
                        pass

                if keys[2] == "state":
                    if int(v) == 0:
                        if self._redis.exists("WashingmachineReady"):
                            self._logger.info("Ack emptying washing machine")
                            self._redis.delete("WashingmachineReady")
                            self._mqclient.publish("bathroom/ttsout", self._template.getAcknowledgeEmtyingWashingMachine())

        if keys[0] == Room.LIVING_ROOM:

            if keys[1] == "button":
                self._logger.info("button")

                #Breakfast
                if v == "1":
                    self._logger.info("Breakfast")

                # Lunch
                if v == "2":
                    self._logger.info("Lunch")

                # Dinner
                if v == "3":
                    self._logger.info("Dinner")

            if keys[1] == "motion":
                self._logger.info("motion in livingroom detected")
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
                            self._logger.info("Waterlevel back to normal")
                            self._mqclient.publish("livingroom/ttsout", self._template.getWaterlevelNormal())
                        else:
                            self._logger.info("Waterlevel is to low now")
                            self._mqclient.publish("livingroom/ttsout", self._template.getWaterlevelLow())
                        self._lastwaterlevel = fval

        if keys[0] == Room.ANSI_ROOM:

            if keys[1] == "button":
                self._logger.info("button")

                #Ansi Read
                if v == "1":
                    self._logger.info("Activating Reading in AnsiRoom")

                    if self._redis.exists("AnsiRoomFallingAsleep"):
                        self._redis.delete("AnsiRoomFallingAsleep")

                    self._redis.setex("AnsiRoomReading", 60 * 60 * 3, time.time())
                    self._mqclient.publish("ansiroom/settemp", "10")

                # Ansi Sleep
                if v == "2":
                    self._logger.info("Activating Sleeping Sequence in AnsiRoom")

                    if self._redis.exists("AnsiRoomReading"):
                        self._redis.delete("AnsiRoomReading")

                    self._redis.setex("AnsiRoomFallingAsleep", 60 * 60 * 5, time.time()) # Will be removed automatically
                    self._mqclient.publish("ansiroom/settemp", "10")

            if keys[1] == "motion":
                self._logger.info("motion in ansi room detected")
                self._redis.setex(Room.ANSI_ROOM+"/populated", 60 * 60, time.time())

                if self._redis.exists("ansiwakeup"):
                    self._logger.info("Ansiwakeup detected motion")
                    self._redis.delete("ansiwakeup")
                    self._mqclient.publish("ansiroom/settemp",                "boost"                             )
                    self._mqclient.publish("ansiroom/bedlight/sleep/sunrise", 0                                   )
                    self._mqclient.publish("ansiroom/ttsout",                 "Good morning ansi"                 )
                    self._mqclient.publish("bathroom/ttsout",                 self._template.getWakeupText("Ansi"))
                    self._mqclient.publish("corridor/light/main",             "TOGGLE"                            )
                    self._mqclient.publish("bathroom/light/main",             "TOGGLE"                            )
                    self._mqclient.publish("coffee/brew_wakeup_coffee",       "NOW"                               )
                    try:
                        Chromecast().volume('Chromeansi', 0.4)
                        Chromecast().playMusicURL('Chromeansi', 'http://rb-bremenvier-live.cast.addradio.de/rb/bremenvier/live/mp3/128/stream.mp3')
                    except Exception as e:
                        self._logger.erro("Error in wakeup")
                        self._logger.error(e)

        if keys[0] == Room.TIFFY_ROOM:

            if keys[1] == "motion":
                self._logger.info("motion in tiffy room detected")
                self._redis.setex(Room.TIFFY_ROOM+"/populated", 60 * 60, time.time())

        if keys[0] == "cortex":

            if keys[1] == "dhcp":
                for entry in json.loads(v):
                    ip = entry['ip'].split(".")
                    if int(ip[3]) > 200 and not self._redis.exists("dynamicdhcpdetected"):
                        self._logger.info("Found new device %s" % entry['name'])
                        self._redis.setex("dynamicdhcpdetected", 60 * 60 * 1, time.time())
                        self._mqclient.publish("ansiroom/ttsout", self._template.getNewDynamicIP(entry['name']))
                        self._mqclient.publish("livingroom/ttsout", self._template.getNewDynamicIP(entry['name']))

            if keys[1] == "dynsilenced":
                self._redis.setex("dynamicdhcpdetected", 60 * 60 * 12, time.time())

    def __init__(self):
        random.seed
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._logger               = logging.getLogger(__name__)
        hdlr                       = logging.FileHandler('/tmp/sensomatic.log')
        formatter                  = logging.Formatter('%(asctime)s %(name)s %(lineno)d %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self._logger.addHandler(hdlr)
        self._logger.setLevel(logging.INFO)
        self._homeDir              = os.path.expanduser("~/.sensomatic")
        self._configFileName       = self._homeDir + '/config.ini'
        self._config               = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient             = mqtt.Client("MqttRulez", clean_session=True)
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

    def _on_connect(self, client, userdata, rc, msg):
        self._logger.info("Connected MQTT Rulez with result code %s" % rc)
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        #self._logger.info("Mq Received on channel %s -> %s" % (msg.topic, msg.payload))
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        self._logger.error("Disconnect MQTTRulez")

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        while True:
            try:
                self._process()
            except Exception as e:
                self._logger.error("Error in processing")
                self._logger.error(e)

if __name__ == '__main__':
    print "Start"

    m = MqttRulez()
    m.start()

    time.sleep(10)

    print "End"