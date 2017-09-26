import os
import sys
import time
import redis
import logging
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
from   Chromecast         import Chromecast
from   Influx             import Influx
from   Adafruit           import Adafruit
from   Exercise           import Exercise

temp      = TemplateMatcher()
info      = InformationFetcher()
logger    = logging.getLogger(__name__)
hdlr      = logging.FileHandler('/tmp/sensomatic.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d %(levelname)s %(message)s')

hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

homeDir        = os.path.expanduser("~/.sensomatic")
configFileName = homeDir + '/config.ini'
config         = ConfigParser.ConfigParser()

def _readConfig():

    update = False

    if not os.path.isdir(homeDir):
        logger.info("Creating homeDir")
        os.makedirs(homeDir)

    if os.path.isfile(configFileName):
        config.read(configFileName)
    else:
        logger.info("Config file not found")
        update = True

    if not config.has_section('MAIN'):
        logger.info("Adding MAIN part")
        update = True
        config.add_section("MAIN")

    if not config.has_section('REDIS'):
        logger.info("Adding Redis part")
        update = True
        config.add_section("REDIS")

    if not config.has_option("REDIS", "ServerAddress"):
        logger.info("No Server Address")
        update = True
        config.set("REDIS", "ServerAddress", "<ServerAddress>")

    if not config.has_option("REDIS", "ServerPort"):
        logger.info("No Server Port")
        update = True
        config.set("REDIS", "ServerPort", "6379")

    if not config.has_section('MQTT'):
        logger.info("Adding MQTT part")
        update = True
        config.add_section("MQTT")

    if not config.has_option("MQTT", "ServerAddress"):
        logger.info("No Server Address")
        update = True
        config.set("MQTT", "ServerAddress", "<ServerAddress>")

    if not config.has_option("MQTT", "ServerPort"):
        logger.info("No Server Port")
        update = True
        config.set("MQTT", "ServerPort", "1883")

    if update:
        with open(configFileName, 'w') as f:
            config.write(f)
            sys.exit(1)

def hourAnnounce():
    logger.info("Announce hour")
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            _mqclient.publish("%s/ttsout" % room, temp.getHourlyTime())

def checkWaschingMachine():
    logger.info("Check washing machine")
    if _redis.exists("WashingmachineReady"):
        logger.info("Washing machine ready")
        timestamp = float(_redis.get("WashingmachineReady"))
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getWashingMachineReady(timestamp))
    else:
        logger.info("Wasching machine inactive")

def goSleep():
    logger.info("Go to sleep")
    _mqclient.publish("livingroom/ttsout", temp.getTimeToGoToBed())

def checkBath():
    logger.info("Checking bath")
    if _redis.exists("PlayRadioInBath") and not info.isSomeoneInTheRoom(Room.BATH_ROOM):
        Mpd().getServerbyName("Bath").stop()
        _mqclient.publish("bathroom/light/rgb", "0,0,0")
        _redis.delete("PlayRadioInBath")

def checkCo2(room):
    logger.info("Check co2")
    for room in Room.ANNOUNCE_ROOMS:
        if info.isSomeoneInTheRoom(room):
            if info.getRoomCo2Level(room) is not None and info.getRoomCo2Level(room) > 2300:
                logger.info("CO2 to high:" + str(info.getRoomCo2Level(room)))
                _mqclient.publish("%s/ttsout" % room, temp.getCo2ToHigh(room))

def radiationCheck():
    logger.info("Radiation check")
    avr  = info.getRadiationAverage()
    here = info.getRadiationForOneStation()
    if here > 0.15:
        _mqclient.publish("telegram", temp.getRadiationToHigh(here))
        for room in Room.ANNOUNCE_ROOMS:
            _mqclient.publish("%s/ttsout" % room, temp.getRadiationToHigh(here))
    if here > avr:
        _mqclient.publish("telegram", temp.getRadiationHigherThenAverage(here, avr))
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getRadiationHigherThenAverage(here, avr))

def particulateMatterCheck():
    logger.info("ParticularMatterCheck")
    p1, p2 = info.getParticulateMatter()
    if p1 > 23.0 or p2 > 23.0:
        _mqclient.publish("telegram", temp.getParticulateMatterHigherThenAverage(p1, p2))
        for room in Room.ANNOUNCE_ROOMS:
            if info.isSomeoneInTheRoom(room):
                _mqclient.publish("%s/ttsout" % room, temp.getParticulateMatterHigherThenAverage(p1, p2))

def bathShowerUpdate():
    logger.info("Checking Bath and Shower conditions")
    if info.getBathOrShower() is not None:
        _mqclient.publish("bathroom/ttsout", temp.getBathShowerUpdate())
    else:
        logger.info("No one showers")

def stopme():
    sys.exit(0)

def _on_connect(client, userdata, rc, msg):
    logger.info("Connected MQTT Main with result code %s" % rc)
    #self._mqclient.subscribe("#")

def _on_message(client, userdata, msg):
    logger.info("Mq Received on channel %s -> %s" % (msg.topic, msg.payload))
    #self._workingQueue.put((msg.topic, msg.payload))

def _on_disconnect(client, userdata, msg):
    logger.error("Disconnect MQTTRulez")


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

    logger.info("Start Persistor")
    persistor = Persistor()
    persistor.start()
    time.sleep(_wait_time)

    logger.info("Start Influx")
    influx = Influx()
    influx.start()
    time.sleep(_wait_time)

    logger.info("Start Telegram bot")
    telegram = Telegram()
    telegram.start()
    time.sleep(_wait_time)

    logger.info("Start MqttRulez")
    rulez = MqttRulez()
    rulez.start()
    time.sleep(_wait_time)

    logger.info("Start Pinger")
    pinger = Pinger()
    pinger.start()
    time.sleep(_wait_time)

    logger.info("Start Cloudant")
    cloudantdb = CloudantDB()
    cloudantdb.start()
    time.sleep(_wait_time)

    logger.info("Start Chromecast")
    chromecast = Chromecast()
    chromecast.start()
    time.sleep(_wait_time)

    logger.info("Start Adafruit")
    adafruit = Adafruit()
    adafruit.start()
    time.sleep(_wait_time)

    logger.info("Start Climate Control")
    climate = Climate()
    climate.start()
    time.sleep(_wait_time)

    logger.info("Start Room Control")
    lightControl = RoomController()
    lightControl.start()
    time.sleep(_wait_time)

    logger.info("Start Alarmclock")
    alarmclock = AlarmClock()
    alarmclock.start()
    time.sleep(_wait_time)

    logger.info("Start Washing Machine")
    washingmachine = HS100("washingmachine", "bathroom/washingmachine/")
    washingmachine.start()
    time.sleep(_wait_time)

    logger.info("Start TwitterPusher")
    twitterpusher = TwitterPusher()
    twitterpusher.start()
    time.sleep(_wait_time)

    logger.info("Start Tank")
    tank = Tank()
    tank.start()
    time.sleep(_wait_time)

    logger.info("Start Coffee machine")
    coffee = SmartCoffee()
    coffee.start()
    time.sleep(_wait_time)

    logger.info("Start Newscatcher")
    newscatcher = Newscatcher()
    newscatcher.start()
    time.sleep(_wait_time)

    logger.info("Start Exercise")
    exercise = Exercise()
    exercise.start()
    time.sleep(_wait_time)

    #https://github.com/dbader/schedule

    schedule.every(23).minutes.do(checkWaschingMachine)
    schedule.every( 1).minutes.do(checkBath)
    schedule.every(30).minutes.do(bathShowerUpdate)

    schedule.every().hour.at("00:00").do(hourAnnounce)
    schedule.every().hour.at("00:42").do(radiationCheck)
    schedule.every().hour.at("00:23").do(particulateMatterCheck)

    schedule.every().day.at("03:23").do(stopme)

    schedule.every(15).minutes.do(checkCo2, Room.ANSI_ROOM)

    schedule.every().sunday.at("22:42").do(goSleep)
    schedule.every().monday.at("22:42").do(goSleep)
    schedule.every().tuesday.at("22:42").do(goSleep)
    schedule.every().wednesday.at("22:42").do(goSleep)
    schedule.every().thursday.at("22:42").do(goSleep)

    while True:
        schedule.run_pending()
        time.sleep(1)
