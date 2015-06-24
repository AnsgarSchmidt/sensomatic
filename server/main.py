import os
import time
import schedule
import ConfigParser
from Tts import Tts
from Template import TemplateMatcher
from Persistor import Persistor
from Room import Room

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

    if update:
        with open(configFileName, 'w') as f:
            config.write(f)

def hourAnnounce(room):
    print "Announce hour"
    tts.createWavFile(temp.getHourlyTime(), room)

def wakeup():
    print "Wakeup"

if __name__ == '__main__':

    _readConfig()

    print "Start Persistor"
    persistor = Persistor()
    persistor.setDaemon(True)
    #persistor.start()

    #https://github.com/dbader/schedule

    schedule.every().hour.do(hourAnnounce, Room.LIVING_ROOM)
    schedule.every().monday.at("05:30").do(wakeup)
    schedule.every().tuesday.at("05:30").do(wakeup)
    schedule.every().wednesday.at("05:30").do(wakeup)
    schedule.every().thursday.at("05:30").do(wakeup)
    schedule.every().friday.at("05:30").do(wakeup)

    hourAnnounce(Room.LIVING_ROOM)

    while True:
        schedule.run_pending()
        time.sleep(1)