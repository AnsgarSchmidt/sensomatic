import os
import time
import redis
import threading
import ConfigParser
from ISStreamer.Streamer import Streamer

class InitialState(threading.Thread):

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

        if not self._config.has_section('INITIALSTATE'):
            print "Adding InitialState part"
            update = True
            self._config.add_section("INITIALSTATE")

        if not self._config.has_option("INITIALSTATE", "accessKey"):
            print "No accessKey"
            update = True
            self._config.set("INITIALSTATE", "accessKey", "<accessKey>")

        if not self._config.has_option("INITIALSTATE", "bucketKey"):
            print "No bucketKey"
            update = True
            self._config.set("INITIALSTATE", "bucketKey", "bucketKey")

        if not self._config.has_option("INITIALSTATE", "bucketName"):
            print "No bucketName"
            update = True
            self._config.set("INITIALSTATE", "bucketName", "bucketName")

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
        self._redis          = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"),
                                                 port=self._config.get("REDIS", "ServerPort"),
                                                 db=0)
        self.connectInitialState()

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

    def connectInitialState(self):
        self.iss = Streamer(bucket_name = self._config.get("INITIALSTATE", "bucketName"),
                            bucket_key  = self._config.get("INITIALSTATE", "bucketKey"),
                            access_key  = self._config.get("INITIALSTATE", "accessKey"),
                            buffer_size = 20)
        self.iss.log("Uplink", "Initial Connect")
        self.iss.flush()

    def pushData(self):
        d = self.getData()

        try:
            self.iss.log("Bathroom Temperature", float(d['bathroom']  ['temperature']       ['value']))
            self.iss.log("Bathroom Humidity",    float(d['bathroom']  ['humidity']          ['value']))
            self.iss.log("Ansiroom Temperature", float(d['ansiroom']  ['temperature']       ['value']))
            self.iss.log("Ansiroom Co2",         float(d['ansiroom']  ['co2']               ['value']))
            self.iss.flush()
        except:
            print "Error reconnect"
            self.connectInitialState()

    def run(self):
        while True:
            self.pushData()
            time.sleep(60)

if __name__ == "__main__":
    print "InitialState"
    i = InitialState()
    i.start()
    time.sleep(10)
