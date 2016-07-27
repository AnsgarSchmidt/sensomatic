import os
import json
import time
import datetime
import threading
import ConfigParser
import paho.mqtt.client   as     mqtt
from   shutil             import copyfile
from   Room               import Room
from   InformationFetcher import InformationFetcher

class Climate(threading.Thread):

    WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

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

        if not self._config.has_section('CLIMA'):
            print "Adding Clima part"
            update = True
            self._config.add_section("CLIMA")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def _checkSettings(self):
        if not os.path.isfile(self._humidityFileName):
            print "Copy new humidity file"
            copyfile("humidity.txt", self._humidityFileName)

        if not os.path.isfile(self._temperatureFileName):
            print "Copy new temperature file"
            copyfile("temperature.txt", self._temperatureFileName)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._humidityFileName       = self._homeDir + '/humidity.txt'
        self._temperatureFileName    = self._homeDir + '/temperature.txt'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._checkSettings()
        self._info                   = InformationFetcher()
        self._mqclient               = mqtt.Client("Climate", clean_session=True)
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop(max_packets=100)

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected with result code %s" % rc

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect"

    def getConfigHumidity(self, room):
        now = datetime.datetime.now()
        data = json.loads(open(self._humidityFileName).read())
        return int(data[room][Climate.WEEKDAYS[now.weekday()]][now.hour])

    def getShouldHumidity(self, room):
        if self._info.getRoomDefinedHumidity(room) is not None:
            return self._info.getRoomDefinedHumidity(room)
        else:
            return self.getConfigHumidity(room)

    def checkHumidity(self):
        for room in Room.ROOMS:
            hum = self._info.getRoomHumidity(room)
            if hum is not None:
                should = self.getShouldHumidity(room)
                print "Humiditycheck room %s. Should is %d and reality is %2.2f" % (room, should, hum)
                if should > hum:
                    print "Humidify now"
                    self._mqclient.publish(room+"/humidifier", 10)

    def getConfigTemperature(self, room):
        now = datetime.datetime.now()
        data = json.loads(open(self._temperatureFileName).read())
        return int(data[room][Climate.WEEKDAYS[now.weekday()]][now.hour])

    def getShouldTemperature(self, room):
        if self._info.getRoomDefinedTemp(room) is not None:
            return self._info.getRoomDefinedTemp(room)
        else:
            return self.getConfigTemperature(room)

    def checkTemperature(self):
        for room in Room.ROOMS:
            temp = self._info.getRoomTemp(room)
            if temp is not None:
                should = self.getShouldTemperature(room)
                print "Temperaturecheck room %s. Should is %d and reality is %2.2f" % (room, should, temp)

    def run(self):
        humwait     = 60
        tempwait    = 10
        humcounter  = humwait
        tempcounter = tempwait

        while True:

            humcounter  -= 1
            tempcounter -= 1

            if humcounter == 0:
                self.checkHumidity()
                humcounter = humwait

            if tempcounter == 0:
                self.checkTemperature()
                tempcounter = tempwait

            self._mqclient.loop()
            time.sleep(1)

if __name__ == '__main__':
    print "Testing climate"
    c = Climate()
    c.start()
    time.sleep(100)