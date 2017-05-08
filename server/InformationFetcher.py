import os
import time
import json
import math
import pytz
import redis
import ephem
import astral
import urllib2
import iso8601
import requests
import httplib2
import datetime
import ConfigParser
from   apiclient         import discovery
from   oauth2client      import client
from   oauth2client      import tools
from   oauth2client.file import Storage
from   requests.auth     import HTTPBasicAuth
from   imapclient        import IMAPClient

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

        if not self._config.has_option("INFORMATION", "Latitude"):
            print "No Latitude"
            update = True
            self._config.set("INFORMATION", "Latitude", "52.5148453")

        if not self._config.has_option("INFORMATION", "Logitude"):
            print "No Logitude"
            update = True
            self._config.set("INFORMATION", "Logitude", "13.4389504")

        if not self._config.has_option("INFORMATION", "Elevation"):
            print "No Elevation"
            update = True
            self._config.set("INFORMATION", "Elevation", "42.23")

        if not self._config.has_option("INFORMATION", "NASAurl"):
            print "No NASAurl"
            update = True
            self._config.set("INFORMATION", "NASAurl", "https://api.nasa.gov/")

        if not self._config.has_option("INFORMATION", "NASAKey"):
            print "No NASAKey"
            update = True
            self._config.set("INFORMATION", "NASAKey", "magic")

        if not self._config.has_option("INFORMATION", "BattleNetKey"):
            print "No BattleNetKey"
            update = True
            self._config.set("INFORMATION", "BattleNetKey", "magic")

        if not self._config.has_option("INFORMATION", "BattleNetSecret"):
            print "No BattleNetSecret"
            update = True
            self._config.set("INFORMATION", "BattleNetSecret", "magic")

        if not self._config.has_option("INFORMATION", "LuftDatenURL"):
            print "No LuftDatenURL"
            update = True
            self._config.set("INFORMATION", "LuftDatenURL", "http://api.luftdaten.info/v1/sensor/")

        if not self._config.has_option("INFORMATION", "LuftDatenSensorID"):
            print "No LuftDatenSensorID"
            update = True
            self._config.set("INFORMATION", "LuftDatenSensorID", "2117")

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

    def getMoonPhase(self, cityName = "Bangkok"):
        #0 = New moon, 7 = First quarter, 14 = Full moon, 21 = Last quarter
        a                  = astral.Astral()
        a.solar_depression = 'civil'
        city               = a[cityName]
        return city.moon_phase(date= datetime.datetime.now(tz = pytz.timezone('Europe/Berlin')))

    def getMoonPosition(self):
        observer = ephem.Observer()
        observer.lon       =       self._config.get("INFORMATION", "Logitude" )
        observer.lat       =       self._config.get("INFORMATION", "Latitude" )
        observer.elevation = float(self._config.get("INFORMATION", "Elevation"))
        observer.date      = datetime.datetime.now(tz = pytz.timezone('Europe/Berlin'))
        moon = ephem.Moon(observer)
        alt = moon.alt * (180 / math.pi)
        az  = moon.az  * (180 / math.pi)
        return alt, az

    def getSunPosition(self):
        observer = ephem.Observer()
        observer.lon       =       self._config.get("INFORMATION", "Logitude" )
        observer.lat       =       self._config.get("INFORMATION", "Latitude" )
        observer.elevation = float(self._config.get("INFORMATION", "Elevation"))
        sun = ephem.Sun(observer)
        alt = sun.alt * (180 / math.pi)
        az  = sun.az  * (180 / math.pi)
        return alt,az

    def getSunTimes(self, cityName = "Bangkok", offset = 11):
        a                  = astral.Astral()
        a.solar_depression = 'civil'
        city               = a[cityName]
        sun                = city.sun(date=datetime.date.today(), local=False)
        dawn               = sun['dawn'].replace(tzinfo=None)    + datetime.timedelta(hours=offset)
        sunrise            = sun['sunrise'].replace(tzinfo=None) + datetime.timedelta(hours=offset)
        noon               = sun['noon'].replace(tzinfo=None)    + datetime.timedelta(hours=offset)
        sunset             = sun['sunset'].replace(tzinfo=None)  + datetime.timedelta(hours=offset)
        dusk               = sun['dusk'].replace(tzinfo=None)    + datetime.timedelta(hours=offset)
        return dawn, sunrise, noon, sunset, dusk

    def getOutsideLightLevel(self):
        # For now just calculated
        sun, _ = self.getSunPosition()
        if sun > 0:
            return (10.0 / 9.0) * sun
        else:
            return 0

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

    def getRoomDefinedTemp(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/settemperature"):
            return float(r.get(room + "/settemperature"))
        else:
            return None

    def getRoomHumidity(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/humidity"):
            return float(r.get(room + "/humidity"))
        else:
            return None

    def getRoomDefinedHumidity(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room + "/sethumidity"):
            return float(r.get(room + "/sethumidity"))
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
        if r.exists("ansiroom/bed/plant"):
            return r.get("ansiroom/bed/plant")
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
        except Exception as e:
            print "Error in getOutdoortemperature"
            print e
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
        return "Ansi or Phawx" # TODO fix name

    def getBathOrShower(self):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists("bath"):
            return "bath"
        if r.exists("shower"):
            return "shower"

    def isSomeoneInTheRoom(self, room):
        r = redis.StrictRedis(host=self._config.get("REDIS","ServerAddress"), port=self._config.get("REDIS","ServerPort"), db=0)
        if r.exists(room+"/populated"):
            last = float(r.get(room+"/populated"))
            if (time.time()) - last < (5 * 60): # 5 min
                return True
        return False

    def getNextWackeuptime(self):
        credential_path     = os.path.join(self._homeDir, 'calendar-python.json')
        secret_path         = os.path.join(self._homeDir, 'client_secret.json'  )
        store               = Storage(credential_path)
        credentials         = store.get()
        if not credentials or credentials.invalid:
            flow            = client.flow_from_clientsecrets(secret_path, 'https://www.googleapis.com/auth/calendar.readonly')
            flow.user_agent = 'Sensomatic Home Automatisation'
            credentials     = tools.run_flow(flow, store)
        http                = credentials.authorize(httplib2.Http())
        service             = discovery.build('calendar', 'v3', http=http)
        now                 = datetime.datetime.utcnow().isoformat() + 'Z'
        eventsResult        = service.events().list(calendarId='hrl7gpmm5u34379e2757kanuhg@group.calendar.google.com', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events              = eventsResult.get('items', [])

        if not events:
            return None, None
        event = events[0]
        start = event['start'].get('dateTime', event['start'].get('date'))
        end   = event['end'].get('dateTime', event['start'].get('date'))
        #print(start, event['summary'])
        return iso8601.parse_date(start), iso8601.parse_date(end)

    def getCheeringLightColours(self):
        try:
            j = json.loads(requests.get("http://api.thingspeak.com/channels/1417/field/2/last.json").content)
            print j
            value = j['field2'].lstrip('#')
            lv = len(value)
            return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)) , j['entry_id']
        except:
            return None, None

    def getSpaceApi(self, spacename):
        try:
            allspaces = json.loads(requests.get("http://spaceapi.fixme.ch/directory.json").content)
            if allspaces is not None and spacename in allspaces:
                url = allspaces[spacename]
                space = json.loads(requests.get(url).content)
                if space is not None:
                    return space
                else:
                    return None
        except:
            return None

    def getParticulateMatter(self):
        p1      = 0.0
        p2      = 0.0
        counter = 0
        try:
            data = json.loads(requests.get(self._config.get("INFORMATION", "LuftDatenURL") + "/" + self._config.get("INFORMATION", "LuftDatenSensorID")).content)
            if data is not None:
                for entry in data:
                    #print json.dumps(entry, indent=4, sort_keys=True)
                    for sensor in entry['sensordatavalues']:
                        if sensor['value_type'] == "P1":
                            p1 += float(sensor['value'])
                        if sensor['value_type'] == "P2":
                            p2 += float(sensor['value'])
                    counter += 1
                p1 /= counter
                p2 /= counter
                p1 = float("{0:.2f}".format(p1))
                p2 = float("{0:.2f}".format(p2))
                return [p1, p2]
            else:
                return [p1, p2]
        except Exception as e:
            print "error"
            print e
            return [p1, p2]

    def isSpaceOpen(self, spacename):
        try:
            space = self.getSpaceApi(spacename)
            if space is not None:
                return bool(space['state']['open'])
        except:
            return None

    def getRadiationAverage(self):
        # https://odlinfo.bfs.de/daten/Datenbereitstellung-2016-04-21.pdf
        try:
            auth = HTTPBasicAuth(self._config.get("INFORMATION","RadiationUser"), self._config.get("INFORMATION","RadiationPasswd"))
            url = self._config.get("INFORMATION","RadiationURL") + "stat.json"
            j = json.loads(requests.get(url, auth=auth).content)
            return j['mwavg']['mw']
        except:
            return 0

    def getRadiationForOneStation(self):
        # https://odlinfo.bfs.de/daten/Datenbereitstellung-2016-04-21.pdf
        try:
            auth = HTTPBasicAuth(self._config.get("INFORMATION","RadiationUser"), self._config.get("INFORMATION","RadiationPasswd"))
            url = self._config.get("INFORMATION","RadiationURL") + self._config.get("INFORMATION","RadiationStation") + "ct.json"
            j = json.loads(requests.get(url, auth=auth).content)
            status = j['stamm']['status']  # 0 defekt, 1 in Betrieb, 128 Testbetrieb, 2048 Wartung
            lastmw = j['stamm']['mw']      # Letzter verfuegbarer (ungepruefter) 1h-Messwert
            mw1h = j['mw1h']
            mw24h = j['mw24h']
            return lastmw
        except:
            return 0

    def getWoWAchievementPoints(self, realm, character):
        try:
            url = "https://us.api.battle.net/wow/character/" + realm + "/" + character + "?fields=stats&locale=en_US&apikey=" + self._config.get("INFORMATION","BattleNetKey")
            j = json.loads(requests.get(url).content)
            return j['achievementPoints']
        except:
            return 0

    def getWoWHealth(self, realm, character):
        try:
            url = "https://us.api.battle.net/wow/character/" + realm + "/" + character + "?fields=stats&locale=en_US&apikey=" + self._config.get("INFORMATION","BattleNetKey")
            j = json.loads(requests.get(url).content)
            return j['stats']['health']
        except:
            return 0

    def getWoWPower(self, realm, character):
        try:
            url = "https://us.api.battle.net/wow/character/" + realm + "/" + character + "?fields=stats&locale=en_US&apikey=" + self._config.get(
                "INFORMATION", "BattleNetKey")
            j = json.loads(requests.get(url).content)
            return j['stats']['power']
        except:
            return 0

    def getWoWTotalHonorableKills(self, realm, character):
        try:
            url = "https://us.api.battle.net/wow/character/" + realm + "/" + character + "?fields=stats&locale=en_US&apikey=" + self._config.get(
                "INFORMATION", "BattleNetKey")
            j = json.loads(requests.get(url).content)
            return j['totalHonorableKills']
        except:
            return 0

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
    #print i.getRoomCo2Level(Room.ANSI_ROOM)
    #print i.getRadiationAverage()
    #print i.getRadiationForOneStation()
    #print i.getSunPosition()
    #print i.getOutsideLightLevel()
    #print i.getNextWackeuptime()
    #print i.getCheeringLightColours()
    #print i.getWoWAchievementPoints("Garrosh", "Phawx")
    #print i.getWoWHealth("Garrosh", "Phawx")
    #print i.getWoWPower("Garrosh", "Phawx")
    #print i.getWoWTotalHonorableKills("Garrosh", "Phawx")
    #print i.getSunTimes("Port Of Spain", 0)
    #print i.getMoonPhase("Port Of Spain")
    #print i.getSunPosition()
    #print i.getMoonPosition()
    #print i.getSpaceApi("xHain")['state']
    #print i.isSpaceOpen("xHain")
    print i.getParticulateMatter()