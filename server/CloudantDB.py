import os
import time
import redis
import threading
import ConfigParser
from   cloudant.client import Cloudant


class CloudantDB(threading.Thread):

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

        if not self._config.has_section('CLOUDANT'):
            print "Adding Cloudant part"
            update = True
            self._config.add_section("CLOUDANT")

        if not self._config.has_option("CLOUDANT", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("CLOUDANT", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("CLOUDANT", "Username"):
            print "No Username"
            update = True
            self._config.set("CLOUDANT", "Username", "Didditulle")

        if not self._config.has_option("CLOUDANT", "Password"):
            print "No Password"
            update = True
            self._config.set("CLOUDANT", "Password", "geheim")

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
        self._redis          = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._cloudant       = Cloudant(self._config.get("CLOUDANT", "Username"), self._config.get("CLOUDANT", "Password"), url=self._config.get("CLOUDANT", "ServerAddress"))
        self.checkDB()

    def checkDB(self):
        self._cloudant.connect()
        if "usshorizon" in self._cloudant.all_dbs():
            self._database = self._cloudant['usshorizon']
            return True
        else:
            print "Create DB"
            self._database = self._cloudant.create_database('usshorizon')
            if self._database.exists():
                print "Success"
                return True
            else:
                print "Error"
                return False

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

    def run(self):
        while True:
            d = self.getData()
            # print d
            try:
                if self.checkDB():
                    self._database.create_document(d)
            except Exception as e:
                print e
                time.sleep(60)
            time.sleep(10)

if __name__ == '__main__':
    c = CloudantDB()
    c.start()
    time.sleep(5)
