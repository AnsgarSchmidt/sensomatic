import os
import time
import redis
import schedule
import ConfigParser
from Tts import Tts
from Template import TemplateMatcher
from Persistor import Persistor
from Room import Room
from MqttRulez import MqttRulez

temp = TemplateMatcher()
tts  = Tts()

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

def hourAnnounce(room):
    print "Announce hour"
    tts.createWavFile(temp.getHourlyTime(), room)

def wakeup():
    print "Wakeup"

def checkWaschingMachine():
    washingtime = (60.0 * 60.0 * 0.5) #normal washing time
    print "Check wasching machine"
    if _redis.exists("Waschingmachine"):
        print "Wasching machine active"
        timestamp = float(_redis.get("Waschingmachine"))
        if (timestamp + washingtime < time.time()):
            print "Waschmaschine ready"
            print temp.getWashingMachineReady(timestamp + washingtime)
    else:
        print "Wasching machine inactive"



if __name__ == '__main__':

    _readConfig()
    _redis         = redis.StrictRedis(host=config.get("REDIS", "ServerAddress"), port=config.get("REDIS", "ServerPort"), db=0)

    print "Start Persistor"
    persistor = Persistor()
    persistor.start()

    print "Start MqttRulez"
    rulez = MqttRulez()
    rulez.start()

    #https://github.com/dbader/schedule

    schedule.every().minutes.do(checkWaschingMachine)
    schedule.every().hour.do(hourAnnounce, Room.LIVING_ROOM)
    schedule.every().monday.at("05:30").do(wakeup)
    schedule.every().tuesday.at("05:30").do(wakeup)
    schedule.every().wednesday.at("05:30").do(wakeup)
    schedule.every().thursday.at("05:30").do(wakeup)
    schedule.every().friday.at("05:30").do(wakeup)

    while True:
        schedule.run_pending()
        time.sleep(1)