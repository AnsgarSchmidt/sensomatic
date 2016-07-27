import os
import time
import json
import redis
import urllib2
import requests
import ConfigParser
from requests.auth import HTTPBasicAuth
from Room import Room
from imapclient import IMAPClient

class InformationFetcher():

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

        if not self._config.has_option("INFORMATION", "RadiationURL"):
            print "No RadiationURL"
            update = True
            self._config.set("INFORMATION", "RadiationURL", "https://odlinfo.bfs.de/daten/json/")

        if not self._config.has_option("INFORMATION", "RadiationUser"):
            print "No RadiationURL"
            update = True
            self._config.set("INFORMATION", "RadiationUser", "USERNAME")

        if not self._config.has_option("INFORMATION", "RadiationPasswd"):
            print "No RadiationURL"
            update = True
            self._config.set("INFORMATION", "RadiationPasswd", "USERPASSWD")

        if not self._config.has_option("INFORMATION", "RadiationStation"):
            print "No RadiationURL"
            update = True
            self._config.set("INFORMATION", "RadiationStation", "110000006")

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
        except Exception as inst:
            print str(inst)
            return 0

    def getRoomTemp(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/temperature"):
            return float(r.get(room + "/temperature"))
        else:
            return None

    def getRoomHumidity(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/humidity"):
            return float(r.get(room + "/humidity"))
        else:
            return None

    def getRoomCo2Level(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/co2"):
            return int(r.get(room + "/co2"))
        else:
            return None

    def getPlantSoilLevel(self):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists("livingroom/plant/soillevel"):
            return r.get("livingroom/plant/soillevel")
        else:
            return None

    def getOutdoor(self):
        '''
            temp, hum, feelslike,  ..... 7
        '''
        try:
            f = urllib2.urlopen(self._config.get("INFORMATION", "WUCurrentURL"))
            json_string = f.read()
            j = json.loads(json_string)
            #print json.dumps(j, sort_keys=True, indent=4, separators=(',', ': '))
            return j["current_observation"]["temp_c"], j["current_observation"]["relative_humidity"], j["current_observation"]["feelslike_c"], j["current_observation"]["weather"], j["current_observation"]["wind_dir"], j["current_observation"]["wind_kph"], j["current_observation"]["wind_gust_kph"]
        except:
            return 0,0,0,0,0,0,0

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
        try:
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
        except:
            return "No valid data"

    def getTimeInBathShower(self):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists("bath"):
            start = float(r.get("bath"))
        if r.exists("shower"):
            start = float(r.get("shower"))
        return int((time.time()-start)/60.0)

    def getWhoIsInBathShower(self):
        return "Ansi"

    def getBathOrShower(self):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists("bath"):
            return "bath"
        if r.exists("shower"):
            return "shower"

    def isSomeoneIsInTheRoom(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room+"/populated"):
            last = float(r.get(room+"/populated"))
            if (time.time()) - last < (15 * 60):
                return True
        return False

    def getCalendar(self):
        SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Google Calendar API Python Quickstart'

    def getRadiationAverage(self):
        # https://odlinfo.bfs.de/daten/Datenbereitstellung-2016-04-21.pdf
        auth = HTTPBasicAuth(self._config.get("INFORMATION","RadiationUser"), self._config.get("INFORMATION","RadiationPasswd"))
        url = self._config.get("INFORMATION","RadiationURL") + "stat.json"
        j = json.loads(requests.get(url, auth=auth).content)
        return j['mwavg']['mw']

    def getRadiationForOneStation(self):
        # https://odlinfo.bfs.de/daten/Datenbereitstellung-2016-04-21.pdf
        auth = HTTPBasicAuth(self._config.get("INFORMATION","RadiationUser"), self._config.get("INFORMATION","RadiationPasswd"))
        url = self._config.get("INFORMATION","RadiationURL") + self._config.get("INFORMATION","RadiationStation") + "ct.json"
        j = json.loads(requests.get(url, auth=auth).content)
        status = j['stamm']['status']  # 0 defekt, 1 in Betrieb, 128 Testbetrieb, 2048 Wartung
        lastmw = j['stamm']['mw']      # Letzter verfuegbarer (ungepruefter) 1h-Messwert
        mw1h = j['mw1h']
        mw24h = j['mw24h']
        return lastmw

if __name__ == '__main__':

    print "Testing"
    i = InformationFetcher()
    #print i.getEarthRotationTime()
    #print i.getNumEmailMessages()
    #print i.getRoomTemp(Room.BATH_ROOM)
    #print i.getRoomHumidity(Room.BATH_ROOM)
    #print i.getOutdoor()
    #print i.getPrediction()
    #print i.getNextISSPass()
    #print i.getAstronauts()
    print i.getRoomCo2Level(Room.ANSI_ROOM)
    print i.getRadiationAverage()
    print i.getRadiationForOneStation()
