import os
import redis
import time
import datetime
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   Room               import Room
from   InformationFetcher import InformationFetcher
from   Chromecast         import Chromecast


class RoomController(threading.Thread):

    def __init__(self):
        self._info = InformationFetcher()
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir          = os.path.expanduser("~/.sensomatic")
        self._configFileName   = self._homeDir + '/config.ini'
        self._config           = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient         = mqtt.Client("RoomController", clean_session=True)
        self._redis            = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"),
                                                   port=self._config.get("REDIS", "ServerPort"), db=0)
        self._lastWorkingLight = [0, 0, 0]
        self._lastBedLight     = [0, 0, 0]
        self._SoundActive      = False
        self._FastCheck        = False

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected Room Controller with result code %s" % rc
        #self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect Room Controller"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        time.sleep(1)

        while True:
            self._FastCheck = True
            self.ansiRoom()

            if self._FastCheck:
                time.sleep(1)
            else:
                time.sleep(30)

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

        if not self._config.has_section('SLEEP'):
            print "Adding SLEEP part"
            update = True
            self._config.add_section("SLEEP")

        if not self._config.has_option("SLEEP", "YoutubeID"):
            print "No YoutubeID Address"
            update = True
            self._config.set("SLEEP", "YoutubeID", "0fYL_qiDYf0")

        if not self._config.has_option("SLEEP", "DurationInMinutes"):
            print "No DurationInMinutes"
            update = True
            self._config.set("SLEEP", "DurationInMinutes", 60)

        if not self._config.has_option("SLEEP", "Volume"):
            print "No Volume"
            update = True
            self._config.set("SLEEP", "Volume", 1.0)

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
        if self._lastWorkingLight[0] != val[0] or self._lastWorkingLight[1] != val[1] or self._lastWorkingLight[2] != val[2]:
            print "Update Workinglight"
            self._mqclient.publish("ansiroom/bedlight/overhead/colour", self.fill(20, [val[0], val[1], val[2]]))
            self._mqclient.publish("ansiroom/bedlight/center/colour",   self.fill(20, [val[0], val[1], val[2]]))
            self._mqclient.publish("ansiroom/bedlight/left/colour",     self.fill(7,  [val[0], val[1], val[2]]))
            self._mqclient.publish("ansiroom/bedlight/right/colour",    self.fill(14, [val[0], val[1], val[2]]))
            self._lastWorkingLight = val

    def setBedLight(self, val):
        if self._lastBedLight[0] != val[0] or self._lastBedLight[1] != val[1] or self._lastBedLight[2] != val[2]:
            self._mqclient.publish("ansiroom/bedlight/sleep/colour",    self.fill(1,  [val[0], val[1], val[2]]))
            self._lastBedLight = val

    def ansiRoom(self):

        if self._redis.exists("AnsiRoomFallingAsleep"):

            self._FastCheck = False

            diff = (time.time() - float(self._redis.get("AnsiRoomFallingAsleep")))
            max  = 60.0 * int(self._config.get("SLEEP", "DurationInMinutes"))

            # Take care of sound
            if not self._SoundActive:
                Chromecast().playYoutube("Chromeansi", self._config.get("SLEEP", "YoutubeID"))
                Chromecast().volume("Chromeansi", float(self._config.get("SLEEP", "Volume")))
                self._SoundActive = True

            if diff <= max:
                percentage = 1.0 - (diff / max)
                light = int(percentage * 255.0)

                if self._lastBedLight[0] != light:
                    self._mqclient.publish("ansiroom/bedlight/sleep/fire", light)
                    self._lastBedLight[0] = light

                val = [light, 0, 0]

                if self._lastWorkingLight[0] != val[0] or self._lastWorkingLight[1] != val[1] or self._lastWorkingLight[2] != val[2]:
                    self._mqclient.publish("ansiroom/bedlight/overhead/colour", self.fill(20, [val[0], val[1], val[2]]))
                    self._mqclient.publish("ansiroom/bedlight/center/colour",   self.fill(20, [val[0], val[1], val[2]]))
                    self._mqclient.publish("ansiroom/bedlight/left/colour",     self.fill(18, [val[0], val[1], val[2]]))
                    self._mqclient.publish("ansiroom/bedlight/right/colour",    self.fill(18, [val[0], val[1], val[2]]))
                    self._lastWorkingLight = val

                Chromecast().volume("Chromeansi", percentage * float(self._config.get("SLEEP", "Volume")))

            # end sequence
            if diff > max:
                print "END Falling Asleep Function"
                self._redis.delete("AnsiRoomFallingAsleep")
                self._mqclient.publish("ansiroom/bedlight/sleep/fire", 0)
                Chromecast().stop('Chromeansi')
                self._SoundActive = False

        elif self._redis.exists("AnsiRoomReading"):

            self._FastCheck = False
            self.setBedLight([150, 150, 10])
            val = [255, 0, 0]

            if self._lastWorkingLight[0] != val[0] or self._lastWorkingLight[1] != val[1] or self._lastWorkingLight[2] != val[2]:
                self._mqclient.publish("ansiroom/bedlight/overhead/colour", self.fill(20, [val[0], val[1], val[2]]))
                self._mqclient.publish("ansiroom/bedlight/center/colour",   self.fill(20, [val[0], val[1], val[2]]))
                self._mqclient.publish("ansiroom/bedlight/left/colour",     self.fill(18, [val[0], val[1], val[2]]))
                self._mqclient.publish("ansiroom/bedlight/right/colour",    self.fill(18, [val[0], val[1], val[2]]))
                self._lastWorkingLight = val

        elif self._info.isSomeoneInTheRoom(Room.ANSI_ROOM):

            self._FastCheck = False
            self.setBedLight([0, 0, 0])
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
                    max = 3.0 * 60.0
                    blue = float(m) / max
                    blue = 1.0 - blue

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
            self.setBedLight([0, 0, 0])

if __name__ == "__main__":
    print "RoomController test"

    l = RoomController()
    l.start()
    time.sleep(23)
