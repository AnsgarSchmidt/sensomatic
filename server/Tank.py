import os
import time
import json
import datetime
import requests
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   InformationFetcher import InformationFetcher
from   Template           import TemplateMatcher
from   requests.auth      import HTTPBasicAuth

SECOND =   1
MINUTE =  60 * SECOND
HOUR   =  60 * MINUTE
DAY    =  24 * HOUR
WEEK   =   7 * DAY
MONTH  =  31 * DAY
YEAR   = 365 * DAY

class Tank(threading.Thread):

    DAWN   = 0
    DAY    = 1
    SUNSET = 2
    NIGHT  = 3

    def _readConfig(self):

        if self._configMTime != os.stat(self._configFileName).st_mtime:

            print "Reread config file for tank"
            self._configMTime = os.stat(self._configFileName).st_mtime
            update = False
            stop   = False

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

            if not self._config.has_section('TANK'):
                print "Adding Tank part"
                update = True
                self._config.add_section("TANK")

            if not self._config.has_option("TANK", "Location"):
                print "No Tank Virtual Location"
                update = True
                self._config.set("TANK", "Location", "Port Of Spain")

            if not self._config.has_option("TANK", "LocationOffset"):
                print "No Tank Virtual Location Offset"
                update = True
                self._config.set("TANK", "LocationOffset", "0")

            if not self._config.has_option("TANK", "NightTemp"):
                print "No Tank Night Temperature"
                update = True
                self._config.set("TANK", "NightTemp", "23")

            if not self._config.has_option("TANK", "DayTemp"):
                print "No Tank Day Temperature"
                update = True
                self._config.set("TANK", "DayTemp", "24")

            if not self._config.has_option("TANK", "FertilizerInterval"):
                print "No Tank FertilizerInterval"
                update = True
                self._config.set("TANK", "FertilizerInterval", "3600")

            if not self._config.has_option("TANK", "GraphInterval"):
                print "No Tank GraphInterval"
                update = True
                self._config.set("TANK", "GraphInterval", "9000")

            if update:
                with open(self._configFileName, 'w') as f:
                    self._config.write(f)

            if stop:
                print "Please check config file"
                sys.exit(0)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir         = os.path.expanduser("~/.sensomatic")
        self._configFileName  = self._homeDir + '/config.ini'
        self._configMTime     = 0
        self._config          = ConfigParser.ConfigParser()
        self._readConfig()
        self._template        = TemplateMatcher()
        self._info            = InformationFetcher()
        self._mqclient        = mqtt.Client("Tank2", clean_session=True)
        self._daystate        = Tank.NIGHT
        self._twitterdaystate = Tank.NIGHT
        self._lastfurtilizer  = time.time()
        self._lastcharts      = time.time()
        self._sunpercentage   = 0
        self._moonpercentage  = 0

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected Tank with result code %s" % rc
        self._mqclient.subscribe("livingroom/tank/#")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        pass

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def updateSunAndMoon(self):
        now                               = datetime.datetime.now()
        dawn, sunrise, noon, sunset, dusk = self._info.getSunTimes(self._config.get("TANK", "Location"), int(self._config.get("TANK", "LocationOffset")))
        moonPhase                         = self._info.getMoonPhase(self._config.get("TANK", "Location"))
        moonElevation, _                  = self._info.getMoonPosition()

        if (dawn < now < sunrise):
            duration = sunrise - dawn
            done     = now - dawn
            self._daystate = Tank.DAWN
            self._sunpercentage = int((done.total_seconds() / duration.total_seconds()) * 100)

        elif (sunrise < now < sunset):
            self._daystate = Tank.DAY
            self._sunpercentage = 100

        elif (sunset < now < dusk):
            duration = dusk - sunset
            done = now - sunset
            self._daystate      = Tank.SUNSET
            self._sunpercentage = int((1.0 - (done.total_seconds() / duration.total_seconds())) * 100)

        else:
            self._daystate      = Tank.NIGHT
            self._sunpercentage = 0

        # 0 = New moon, 7 = First quarter, 14 = Full moon, 21 = Last quarter
        moonphasepercentage = 0.0

        if (0 <= moonPhase <= 14):
            moonphasepercentage = 1.0 - ( (14.0 - (moonPhase       ) ) / 14.0)
        else:
            moonphasepercentage =       ( (14.0 - (moonPhase - 14.0) ) / 14.0)

        if moonElevation > 0:
            self._moonpercentage = int(moonphasepercentage * (moonElevation / 90.0) * 100)
        else:
            self._moonpercentage = 0

    def publishMQTT(self):
        self._mqclient.publish("livingroom/tank/whitelight", self._sunpercentage )
        self._mqclient.publish("livingroom/tank/bluelight",  self._moonpercentage)

        if self._daystate in (Tank.DAWN, Tank.DAY, Tank.SUNSET):
            self._mqclient.publish("livingroom/tank/settemp",   self._config.get("TANK", "DayTemp"))
        else:
            self._mqclient.publish("livingroom/tank/settemp",   self._config.get("TANK", "NightTemp"))

    def publishTwitter(self):
        if self._twitterdaystate is not self._daystate:
            if self._daystate == Tank.DAWN:
                self._mqclient.publish("twitter/text", "Switching light scene to dawn and rise the light level. #Fishtank Yellow #cheerlights")
            if self._daystate == Tank.DAY:
                self._mqclient.publish("twitter/text", "Switching light scene to day. #Fishtank Warmwhite #cheerlights")
            if self._daystate == Tank.SUNSET:
                self._mqclient.publish("twitter/text", "Switching light scene to sunset and lover the light level. #Fishtank Orange #cheerlights")
            if self._daystate == Tank.NIGHT:
                self._mqclient.publish("twitter/text", "Switching light scene to night. #Fishtank Black #cheerlights")
            self._twitterdaystate = self._daystate

    def publishFertilizer(self):
        now = time.time()
        if self._daystate == Tank.DAY:
            if (now - self._lastfurtilizer) > int(self._config.get("TANK", "FertilizerInterval")):
                self._mqclient.publish("livingroom/tank/fertilizer", 1)
                self._mqclient.publish("twitter/text", "Adding some material of natural or synthetic origin (other than liming materials). #Fishtank #Fertilizer")
                self._lastfurtilizer = now

    def publishCharts(self):
        now = time.time()
        if (now - self._lastcharts) > int(self._config.get("TANK", "GraphInterval")):
            try:
                j = json.loads(requests.get("https://uss-horizon.mybluemix.net/api/twitter/getHeaterID").content)
                self._mqclient.publish("twitter/uploaded/" + j[0]['media_id_string'], "Water temperature, air temperature, heater active and water level. #IoT #Fishtank #watson #analytics")
                self._mqclient.publish("twitter/uploaded/" + j[1]['media_id_string'], "Heater activity percentage, air temperature and humidity. #IoT #Fishtank #watson #analytics")
                self._mqclient.publish("twitter/uploaded/" + j[2]['media_id_string'], "Sun and moon intensity for the fishtank. #IoT #fishtank #watson #analytics")
            except:
                print "Error in publishing charts"
            self._lastcharts = now

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()

        while True:
            self._readConfig()
            self.updateSunAndMoon()
            self.publishMQTT()
            self.publishTwitter()
            self.publishFertilizer()
            self.publishCharts()
            time.sleep(15)

if __name__ == '__main__':
    print "Start"
    t = Tank()
    t.start()
    time.sleep(100)
    print "End"
