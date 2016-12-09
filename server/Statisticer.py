import json
import requests
import os
import time
import threading
import ConfigParser

from requests.auth     import HTTPBasicAuth

SECOND =  1
MINUTE = 60 * SECOND
HOUR   = 60 * MINUTE
DAY    = 24 * HOUR
WEEK   =  7 * DAY

class Statisticer(threading.Thread):

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

    def get1Week(self):
        return self.getCloudantData(time.time() - WEEK, time.time())

    def get24Hours(self):
        return self.getCloudantData(time.time() -  DAY, time.time())

    def get1Hour(self):
        return self.getCloudantData(time.time() -  HOUR, time.time())

    def getCloudantData(self, start, end):
        auth = HTTPBasicAuth(self._config.get("CLOUDANT", "username"),
                             self._config.get("CLOUDANT", "password"))
        url = "%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (self._config.get("CLOUDANT", "serveraddress"), start, end)
        j = json.loads(requests.get(url, auth=auth).content)
        return j['rows']

    def calculateCharts(self):
        data = self.get1Week()
        print len(data)

    def run(self):
        while True:
            self.calculateCharts()
            time.sleep(10)


if __name__ == '__main__':
    c = Statisticer()
    c.start()
    time.sleep(23)