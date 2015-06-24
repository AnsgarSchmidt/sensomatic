import os
import time
import json
import redis
import urllib2
import ConfigParser
from imapclient import IMAPClient

class InformationFetcher():

    BATH="badezimmer"
    LIVING="livingroom"
    ANSI="ansi"
    TIFFY="tiffy"

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

        if not self._config.has_section('INFORMATION'):
            print "Adding MQTT part"
            update = True
            self._config.add_section("INFORMATION")

        if not self._config.has_option("INFORMATION", "IMAPServer"):
            print "No Server Address"
            update = True
            self._config.set("INFORMATION", "IMAPServer", "<ServerAddress>")

        if not self._config.has_option("INFORMATION", "IMAPUser"):
            print "No Username"
            update = True
            self._config.set("INFORMATION", "IMAPUser", "<IMAPUser>")

        if not self._config.has_option("INFORMATION", "IMAPPasswd"):
            print "No Passwd"
            update = True
            self._config.set("INFORMATION", "IMAPPasswd", "<IMAPPasswd>")

        if not self._config.has_option("INFORMATION", "IMAPFolder"):
            print "No Folder"
            update = True
            self._config.set("INFORMATION", "IMAPFolder", "<IMAPFolder>")

        if not self._config.has_option("INFORMATION", "WUCurrentURL"):
            print "No URL"
            update = True
            self._config.set("INFORMATION", "WUCurrentURL", "<WU Current>")

        if not self._config.has_option("INFORMATION", "WUPredictionURL"):
            print "No URL"
            update = True
            self._config.set("INFORMATION", "WUPredictionURL", "<WU Predict>")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

    def getEarthRotationTime(self):
        seconds  = time.gmtime().tm_sec         *  1.0
        seconds += time.gmtime().tm_min         * 60.0
        seconds += time.gmtime().tm_hour * 60.0 * 60.0
        fraction = 360.0 * (seconds / (60.0 * 60.0 * 24.0 * 1.0) )

        degrees = int(   fraction                                    )
        minutes = int(  (fraction - degrees) * 60.0                  )
        seconds = int( ((fraction - degrees) * 60.0 - minutes) * 60.0)
        return fraction, degrees, minutes, seconds

    def getNumEmailMessages(self):
        try:
            server = IMAPClient(self._config.get("INFORMATION","IMAPServer"), use_uid=True, ssl=True)
            server.login(self._config.get("INFORMATION", "IMAPUser"), self._config.get("INFORMATION", "IMAPPasswd"))
            select_info = server .select_folder(self._config.get("INFORMATION", "IMAPFolder"))
            #print json.dumps(select_info, sort_keys=True, indent=4, separators=(',', ': '))
            return select_info['EXISTS']
        except:
            return 0

    def getRoomTemp(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/temperature"):
            return r.get(room + "/temperature")
        else:
            return None

    def getRoomHumidity(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/humidity"):
            return r.get(room + "/humidity")
        else:
            return None

    def getOutdoor(self):
        f = urllib2.urlopen(self._config.get("INFORMATION", "WUCurrentURL"))
        json_string = f.read()
        j = json.loads(json_string)
        #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
        return j["current_observation"]["temp_c"], j["current_observation"]["relative_humidity"], j["current_observation"]["feelslike_c"], j["current_observation"]["weather"], j["current_observation"]["wind_dir"], j["current_observation"]["wind_kph"], j["current_observation"]["wind_gust_kph"]

    def getPrediction(self):
        f = urllib2.urlopen(self._config.get("INFORMATION","WUPredictionURL"))
        json_string = f.read()
        j = json.loads(json_string)
        #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
        return j['forecast']['txt_forecast']['forecastday'][0]['fcttext_metric']

    def getNextISSPass(self):
        f = urllib2.urlopen("http://api.open-notify.org/iss-pass.json?lat=52.5147&lon=13.4394&alt=80&n=10")
        j = json.loads(f.read())
        #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
        passes = []
        for i in j['response']:
            if int(i['duration']) > 600:
                passes.append(int(i['risetime']))
        return passes

    def getAstronauts(self):
        f = urllib2.urlopen("http://api.open-notify.org/astros.json")
        j = json.loads(f.read())
        #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
        num = int(j['number'])
        ast = ""
        for i in range(num - 1):
                ast = ast +  j['people'][i]['name'] + ', '
        ast = ast[:-2]
        ast = ast + " and "
        ast = ast + j['people'][num - 1]['name']

        return ast

if __name__ == '__main__':

    print "Testing"
    i = InformationFetcher()
    #print i.getEarthRotationTime()
    #print i.getNumEmailMessages()
    #print i.getRoomTemp(InformationFetcher.BATH)
    #print i.getRoomHumidity(InformationFetcher.BATH)
    #print i.getOutdoor()
    #print i.getPrediction()
    print i.getNextISSPass()
    print i.getAstronauts()
