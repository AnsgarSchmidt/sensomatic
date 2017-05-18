import os
import json
import time
import pytz
import requests
import datetime
import threading
import ConfigParser
import matplotlib.pyplot as     plt
from   requests.auth     import HTTPBasicAuth

SECOND =   1
MINUTE =  60 * SECOND
HOUR   =  60 * MINUTE
DAY    =  24 * HOUR
WEEK   =   7 * DAY
MONTH  =  31 * DAY
YEAR   = 365 * DAY

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
        plt.rcdefaults()

    def getAll(self):
        return self.getCloudantData(time.time() - 10 * YEAR, time.time())

    def get1Year(self):
        return self.getCloudantData(time.time() - YEAR, time.time())

    def get1Month(self):
        return self.getCloudantData(time.time() - MONTH, time.time())

    def get1Week(self):
        return self.getCloudantData(time.time() - WEEK, time.time())

    def get1Day(self):
        return self.getCloudantData(time.time() -  DAY, time.time())

    def get1Hour(self):
        return self.getCloudantData(time.time() -  HOUR, time.time())

    def getCloudantData(self, start, end):
        auth = HTTPBasicAuth(self._config.get("CLOUDANT", "username"),
                             self._config.get("CLOUDANT", "password"))
        url = "%s/usshorizon/_design/livingroom/_view/cortex?descending=false&startkey=%f&endkey=%f" % (self._config.get("CLOUDANT", "serveraddress"), start, end)
        j = json.loads(requests.get(url, auth=auth).content)
        return j['rows']

    def calculateDelta(self, data):
        newdata = []
        for i in range(len(data) - 1):
            k = i + 1
            traffic = False
            for net in ['WAN','5G','2.4G']:
                for direction in ['RX','TX']:
                    current = int(data[k    ]['value'][net][direction])
                    before  = int(data[k - 1]['value'][net][direction])
                    val = (current - before)
                    if val < 0:
                        val = current
                    if val > 0:
                        traffic = True
                    data[k]['value'][net][direction+'DELTA'] = val
            if traffic:
                newdata.append(data[k])
        return newdata

    def calculateCharts(self):
        data = self.get1Hour()
        newdata = self.calculateDelta(data)
        timekey = []
        wan_rx  = []
        wan_tx  = []
        new_tx  = []
        new_rx  = []
        old_tx  = []
        old_rx  = []
        tz = pytz.timezone('Europe/Berlin')
        for i in range(len(newdata)):
            timekey.append(datetime.datetime.fromtimestamp(newdata[i]['key'], tz=tz))
            wan_rx.append (newdata[i]['value']['WAN']['RXDELTA'])
            wan_tx.append (newdata[i]['value']['WAN']['TXDELTA'])
            new_rx.append (newdata[i]['value']['5G']['RXDELTA'])
            new_tx.append (newdata[i]['value']['5G']['TXDELTA'])
            old_rx.append (newdata[i]['value']['2.4G']['RXDELTA'])
            old_tx.append (newdata[i]['value']['2.4G']['TXDELTA'])

        f, axarr = plt.subplots(2, 3)
        axarr[0, 0].plot(timekey, wan_rx)
        axarr[0, 0].set_title('wan rx')
        axarr[1, 0].plot(timekey, wan_tx)
        axarr[1, 0].set_title('wan tx')
        axarr[0, 1].plot(timekey, new_rx)
        axarr[0, 1].set_title('5g rx')
        axarr[1, 1].plot(timekey, new_tx)
        axarr[1, 1].set_title('5g tx')
        axarr[0, 2].plot(timekey, old_rx)
        axarr[0, 2].set_title('2.4g rx')
        axarr[1, 2].plot(timekey, old_tx)
        axarr[1, 2].set_title('2.4g tx')

        for x in range(1):
            for y in range(2):
                for label in axarr[x, y].xaxis.get_ticklabels():
                    label.set_visible(False)

                for label in axarr[x, y].xaxis.get_ticklabels()[::2]:
                    label.set_visible(True)

        plt.draw()
        plt.savefig('tessstttyyy.png', dpi = 256)
        print "END"

    def run(self):
        while True:
            self.calculateCharts()
            time.sleep(1000)

if __name__ == '__main__':
    c = Statisticer()
    c.start()
    time.sleep(60)