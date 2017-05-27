import os
import sys
import time
import redis
import schedule
import ConfigParser
import paho.mqtt.client   as     mqtt
from   CloudantDB         import CloudantDB
from   InformationFetcher import InformationFetcher
from   Template           import TemplateMatcher
from   Persistor          import Persistor
from   Room               import Room
from   MqttRulez          import MqttRulez
from   Pinger             import Pinger
from   Climate            import Climate
from   RoomController     import RoomController
from   AlarmClock         import AlarmClock
from   HS100              import HS100
from   Mpd                import Mpd
from   TwitterPusher      import TwitterPusher
from   Tank               import Tank
from   Telegram           import Telegram
from   SmarterCoffee      import SmartCoffee
from   Newscatcher        import Newscatcher

temp = TemplateMatcher()
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

    if not config.has_section('MQTT'):
        print "Adding MQTT part"
        update = True
        config.add_section("MQTT")

    if not config.has_option("MQTT", "ServerAddress"):
        print "No Server Address"
        update = True
        config.set("MQTT", "ServerAddress", "<ServerAddress>")

    if not config.has_option("MQTT", "ServerPort"):
        print "No Server Port"
        update = True
        config.set("MQTT", "ServerPort", "1883")

    if update:
        with open(configFileName, 'w') as f:
            config.write(f)
            sys.exit(1)

def hourAnnounce():
    print "Announce hour"
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            _mqclient.publish("%s/ttsout" % room, temp.getHourlyTime())

def checkWaschingMachine():
    print "Check washing machine"
    if _redis.exists("WashingmachineReady"):
        print "Washing machine ready"
        timestamp = float(_redis.get("WashingmachineReady"))
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getWashingMachineReady(timestamp))
    else:
        print "Wasching machine inactive"

def goSleep():
    print "Go to sleep"
    _mqclient.publish("livingroom/ttsout", temp.getTimeToGoToBed())

def checkBath():
    print "Checking bath"
    if _redis.exists("PlayRadioInBath") and not info.isSomeoneInTheRoom(Room.BATH_ROOM):
        Mpd().getServerbyName("Bath").stop()
        _mqclient.publish("bathroom/light/rgb", "0,0,0")
        _redis.delete("PlayRadioInBath")

def checkCo2(room):
    print "Check co2"
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            if info.getRoomCo2Level(room) is not None and info.getRoomCo2Level(room) > 2300:
                print "CO2 to high:" + str(info.getRoomCo2Level(room))
                _mqclient.publish("%s/ttsout" % room, temp.getCo2ToHigh(room))

def radiationCheck():
    print "Radiation check"
    avr  = info.getRadiationAverage()
    here = info.getRadiationForOneStation()
    if here > 0.15:
        for room in Room.ANNOUNCE_ROOMS:
            _mqclient.publish("%s/ttsout" % room, temp.getRadiationToHigh(here))
    if here > avr:
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getRadiationHigherThenAverage(here, avr))

def particulateMatterCheck():
    print "ParticularMatterCheck"
    p1, p2 = info.getParticulateMatter()
    if p1 > 23.0 or p2 > 23.0:
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getParticulateMatterHigherThenAverage(p1, p2))

def bathShowerUpdate():
    print "Checking Bath and Shower conditions"
    if info.getBathOrShower() is not None:
        _mqclient.publish("bathroom/ttsout", temp.getBathShowerUpdate())
    else:
        print "No one showers"

def _on_connect(client, userdata, rc, msg):
    print "Connected MQTT Main with result code %s" % rc
    #self._mqclient.subscribe("#")

def _on_message(client, userdata, msg):
    print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
    #self._workingQueue.put((msg.topic, msg.payload))

def _on_disconnect(client, userdata, msg):
    print "Disconnect MQTTRulez"


if __name__ == '__main__':
    _readConfig()
    _redis                  = redis.StrictRedis(host=config.get("REDIS", "ServerAddress"), port=config.get("REDIS", "ServerPort"), db=0)
    _mqclient               = mqtt.Client("Main", clean_session=True)
    _mqclient.connect(config.get("MQTT", "ServerAddress"), config.get("MQTT", "ServerPort"), 60)
    _mqclient.on_connect    = _on_connect
    _mqclient.on_message    = _on_message
    _mqclient.on_disconnect = _on_disconnect
    _mqclient.loop_start()
    _wait_time = 5

    print "Start Persistor"
    persistor = Persistor()
    persistor.start()
    time.sleep(_wait_time)

    #print "Start Carbon"
    #carbon = Carbon()
    #carbon.start()
    #time.sleep(_wait_time)

    print "Start Telegram bot"
    telegram = Telegram()
    telegram.start()
    time.sleep(_wait_time)

    print "Start MqttRulez"
    rulez = MqttRulez()
    rulez.start()
    time.sleep(_wait_time)

    print "Start Pinger"
    pinger = Pinger()
    pinger.start()
    time.sleep(_wait_time)

    print "Start Cloudant"
    cloudantdb = CloudantDB()
    cloudantdb.start()
    time.sleep(_wait_time)

    #print "Start Inital State"
    #initialState = InitialState()
    #initialState.start()
    #time.sleep(_wait_time)

    print "Start Climate Control"
    climate = Climate()
    climate.start()
    time.sleep(_wait_time)

    print "Start Room Control"
    lightControl = RoomController()
    lightControl.start()
    time.sleep(_wait_time)

    print "Start Alarmclock"
    alarmclock = AlarmClock()
    alarmclock.start()
    time.sleep(_wait_time)

    print "Start Washing Machine"
    washingmachine = HS100("washingmachine", "bathroom/washingmachine/")
    washingmachine.start()
    time.sleep(_wait_time)

    print "Start TwitterPusher"
    twitterpusher = TwitterPusher()
    twitterpusher.start()
    time.sleep(_wait_time)

    print "Start Tank"
    tank = Tank()
    tank.start()
    time.sleep(_wait_time)

    print "Start Coffee machine"
    coffee = SmartCoffee()
    coffee.start()
    time.sleep(_wait_time)

    print "Start Newscatcher"
    newscatcher = Newscatcher()
    newscatcher.start()
    time.sleep(_wait_time)

    #https://github.com/dbader/schedule

    schedule.every(15).minutes.do(checkWaschingMachine)
    schedule.every( 1).minutes.do(checkBath)
    schedule.every(30).minutes.do(bathShowerUpdate)

    schedule.every().hour.at("00:00").do(hourAnnounce)
    schedule.every().hour.at("00:42").do(radiationCheck)
    schedule.every().hour.at("00:23").do(particulateMatterCheck)

    schedule.every(15).minutes.do(checkCo2, Room.ANSI_ROOM)

    schedule.every().sunday.at("22:42").do(goSleep)
    schedule.every().monday.at("22:42").do(goSleep)
    schedule.every().tuesday.at("22:42").do(goSleep)
    schedule.every().wednesday.at("22:42").do(goSleep)
    schedule.every().thursday.at("22:42").do(goSleep)

    while True:
        schedule.run_pending()
        time.sleep(1)
