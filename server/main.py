import os
import time
import redis
import schedule
import ConfigParser
from   Cloudant           import Cloudant
from   InformationFetcher import InformationFetcher
from   Tts                import Tts
from   Template           import TemplateMatcher
from   Persistor          import Persistor
from   Room               import Room
from   MqttRulez          import MqttRulez
from   Pinger             import Pinger
from   InitialState       import InitialState
from   Climate            import Climate
from   LightController    import LightController
from   AlarmClock         import AlarmClock
from   HS100              import HS100

temp = TemplateMatcher()
tts  = Tts()
info = InformationFetcher()

homeDir        = os.path.expanduser("~/.sensomatic")
configFileName = homeDir + '/config.ini'
config         = ConfigParser.ConfigParser()

def _readConfig():

    update = False

    if not os.path.isdir(homeDir):
        print "Creating homeDir"
        os.makedirs(homeDir)

    if os.path.isfile(configFileName):
        config.read(configFileName)
    else:
        print "Config file not found"
        update = True

    if not config.has_section('MAIN'):
        print "Adding MAIN part"
        update = True
        config.add_section("MAIN")

    if not config.has_section('REDIS'):
        print "Adding Redis part"
        update = True
        config.add_section("REDIS")

    if not config.has_option("REDIS", "ServerAddress"):
        print "No Server Address"
        update = True
        config.set("REDIS", "ServerAddress", "<ServerAddress>")

    if not config.has_option("REDIS", "ServerPort"):
        print "No Server Port"
        update = True
        config.set("REDIS", "ServerPort", "6379")

    if update:
        with open(configFileName, 'w') as f:
            config.write(f)

def hourAnnounce():
    print "Announce hour"
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            tts.createWavFile(temp.getHourlyTime(), room)

def checkWaschingMachine():
    print "Check washing machine"
    if _redis.exists("WashingmachineReady"):
        print "Washing machine ready"
        timestamp = float(_redis.get("WashingmachineReady"))
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                tts.createWavFile(temp.getWashingMachineReady(timestamp), room)
    else:
        print "Wasching machine inactive"

def goSleep():
    print "Go to sleep"
    tts.createWavFile(temp.getTimeToGoToBed(), Room.LIVING_ROOM)

def checkBath():
    print "Checking bath"

def checkCo2(room):
    print "Check co2"
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            if info.getRoomCo2Level(room) is not None and info.getRoomCo2Level(room) > 2200:
                print "CO2 to high:" + str(info.getRoomCo2Level(room))
                tts.createWavFile(temp.getCo2ToHigh(room), room)

def radiationCheck():
    print "Radiation check"
    avr  = info.getRadiationAverage()
    here = info.getRadiationForOneStation()
    if here > 0.15:
        for room in Room.ANNOUNCE_ROOMS:
            tts.createWavFile(temp.getRadiationToHigh(here), room)
    if here > avr:
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                tts.createWavFile(temp.getRadiationHigherThenAverage(here,avr), room)

def bathShowerUpdate():
    print "Checking Bath and Shower conditions"
    if info.getBathOrShower() is not None:
        tts.createWavFile(temp.getBathShowerUpdate(), Room.BATH_ROOM)
    else:
        print "No one showers"

if __name__ == '__main__':

    _readConfig()
    _redis = redis.StrictRedis(host=config.get("REDIS", "ServerAddress"), port=config.get("REDIS", "ServerPort"), db=0)

    print "Start Persistor"
    persistor = Persistor()
    persistor.start()

    print "Start MqttRulez"
    rulez = MqttRulez()
    rulez.start()

    print "Start Pinger"
    pinger = Pinger()
    pinger.start()

    print "Start Cloudant"
    cloudantdb = Cloudant()
    cloudantdb.start()

    print "Start Inital State"
    initialState = InitialState()
    initialState.start()

    print "Start Climate Control"
    climate = Climate()
    climate.start()

    print "Start Light Control"
    lightControl = LightController()
    lightControl.start()

    print "Start Alarmclock"
    alarmclock = AlarmClock()
    alarmclock.start()

    print "Start Washing Machine"
    washingmachine = HS100("192.168.1.42", "bathroom/washingmachine/")
    washingmachine.start()

    #https://github.com/dbader/schedule

    schedule.every(15).minutes.do(checkWaschingMachine)
    schedule.every(10).minutes.do(checkBath)
    schedule.every(30).minutes.do(bathShowerUpdate)

    schedule.every().hour.at("00:00").do(hourAnnounce)
    schedule.every().hour.at("00:42").do(radiationCheck)

    schedule.every(15).minutes.do(checkCo2, Room.ANSI_ROOM)

    schedule.every().sunday.at("22:42").do(goSleep)
    schedule.every().monday.at("22:42").do(goSleep)
    schedule.every().tuesday.at("22:42").do(goSleep)
    schedule.every().wednesday.at("22:42").do(goSleep)
    schedule.every().thursday.at("22:42").do(goSleep)

    while True:
        schedule.run_pending()
        time.sleep(1)
