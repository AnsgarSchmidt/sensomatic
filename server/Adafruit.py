import os
import time
import redis
import threading
import ConfigParser
from   Adafruit_IO      import Client


class Adafruit(threading.Thread):

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

        if not self._config.has_section('ADAFRUIT'):
            print "Adding ADAFRUIT part"
            update = True
            self._config.add_section("ADAFRUIT")

        if not self._config.has_option("ADAFRUIT", "Id"):
            print "No Adafruit Id"
            update = True
            self._config.set("ADAFRUIT", "Id", "<Id>")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._redis          = redis.StrictRedis(host= self._config.get("REDIS", "ServerAddress"),
                                                 port= self._config.get("REDIS", "ServerPort"),
                                                 db  = 0)
        self._adafruit       = Client(self._config.get("ADAFRUIT", "Id"))

    def getData(self):
        data = {'timestamp':time.time()}
        for key in self._redis.keys():
            k = key.split('/')
            l = len(k)
            w = data
            for i in range(l):
                if k[i] not in w:
                    w[k[i]] = {}
                w = w[k[i]]
                if i == l - 1:
                    w['value'] = self._redis.get(key)
        return data

    def pushData(self):
        d = self.getData()
        try:
            if "bathroom" in d:
                if "temperature" in d['bathroom']:
                    self._adafruit.send("Bathroom Temperature",          float(d['bathroom']                      ['temperature'] ['value']))
                    self._adafruit.send("Bathroom Humidity",             float(d['bathroom']                      ['humidity']    ['value']))
                    self._adafruit.send("Bathroom Combustible",          float(d['bathroom']                      ['combustible'] ['value']))
                if "washingmachine" in d['bathroom']:
                    self._adafruit.send("Bathroom Wachingmachine Power", float(d['bathroom']   ['washingmachine'] ['current']     ['value']))
            if "ansiroom" in d:
                self._adafruit.send("Ansiroom Temperature",              float(d['ansiroom']                      ['temperature'] ['value']))
                self._adafruit.send("Ansiroom Co2",                      float(d['ansiroom']                      ['co2']         ['value']))
            if "livingroom" in d:
                if "tank" in d['livingroom']:
                    self._adafruit.send("Livingroom Temperature",        float(d['livingroom'] ['tank']           ['airtemp']     ['value']))
                    self._adafruit.send("Livingroom Humidity",           float(d['livingroom'] ['tank']           ['humidity']    ['value']))
                    self._adafruit.send("Tank Temperature",              float(d['livingroom'] ['tank']           ['watertemp']   ['value']))
        except Exception as e:
            print "Error in Adafruit"
            print e

    def run(self):
        while True:
            self.pushData()
            time.sleep(23)

if __name__ == "__main__":
    print "Adafruit"
    a = Adafruit()
    a.start()
    time.sleep(462)
