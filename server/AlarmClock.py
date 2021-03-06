import os
import sys
import time
import redis
import logging
import threading
import ConfigParser
import datetime
import paho.mqtt.client   as     mqtt
from   pytz               import timezone
from   InformationFetcher import InformationFetcher

class AlarmClock(threading.Thread):

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

        if not self._config.has_section('REDIS'):
            print "Adding Redis part"
            update = True
            self._config.add_section("REDIS")

        if not self._config.has_option("REDIS", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("REDIS", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("REDIS", "ServerPort"):
            print "No Server Port"
            update = True
            self._config.set("REDIS", "ServerPort", "6379")

        if not self._config.has_section('MQTT'):
            print "Adding MQTT part"
            update = True
            self._config.add_section("MQTT")

        if not self._config.has_option("MQTT", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("MQTT", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("MQTT", "ServerPort"):
            print "No Server Port"
            update = True
            self._config.set("MQTT", "ServerPort", "1883")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit(1)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._logger                 = logging.getLogger(__name__)
        hdlr                         = logging.FileHandler('/tmp/sensomatic.log')
        formatter                    = logging.Formatter('%(asctime)s %(name)s %(lineno)d %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self._logger.addHandler(hdlr)
        self._logger.setLevel(logging.INFO)
        self._info                   = InformationFetcher()
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._redis                  = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"), port=self._config.get("REDIS", "ServerPort"), db=0)
        self._mqclient               = mqtt.Client("AlarmClock", clean_session=True)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.loop_start()

    def _on_connect(self, client, userdata, rc, msg):
        self._logger.info("Connected Alarmclock with result code %s" % rc)

    def _on_message(self, client, userdata, msg):
        self._logger.info("Mq Received on channel %s -> %s" % (msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        self._logger.warn("Disconnect Alarmclock")

    def run(self):
        starttime, endtime = self._info.getNextWackeuptime()
        updated            = time.time()
        waking             = False
        music              = False

        while True:
            diff = (starttime - datetime.datetime.now(timezone('Europe/Berlin'))).total_seconds()

            #Switch on the light 15 min before event
            if 0 < diff < (60 * 15):
                lightlevel = int((1.0 - (diff / (60 * 15))) * 100)
                self._logger.info("switching or engreasing lightlevel to %d " % lightlevel)
                self._mqclient.publish("ansiroom/bedlight/sleep/sunrise", lightlevel)
                waking = True

            #5 Min before slowly turn on the music
            if 0 < diff < (60 * 5):
                if not music:
                    try:
                        self._logger.info("Switching on the music")
                        self._mqclient.publish("chromecast/Chromeansi/volume", 0.0)
                        self._mqclient.publish("chromecast/Chromeansi/playMusicURL", "http://inforadio.de/livemp3")
                        music = True
                    except Exception as e:
                        self._logger.error("Error in starting the music")
                        self._logger.error(e)
                        music = False
                volume = (1.0 - (diff / (60 * 5))) * 0.6
                try:
                    self._logger.info("Setting the volume to %d" % volume)
                    self._mqclient.publish("chromecast/Chromeansi/volume", volume)
                except Exception as e:
                    self._logger.error("Error in setting the volume")
                    self._logger.error(e)

            if diff < 0 and waking:
                self._logger.info("Switching light to max")
                self._mqclient.publish("ansiroom/bedlight/sleep/sunrise", 100)
                try:
                    self._logger.info("Switching volume to max");
                    self._mqclient.publish("chromecast/Chromeansi/volume", 0.7)
                except Exception as e:
                    self._logger.error("Error in setting max volume")
                    self._logger.error(e)
                waking = False
                music  = False
                self._logger.info("Wakeup done")
                self._redis.setex("ansiwakeup", 60 * 60 * 6, time.time())

            if (time.time() - updated) > (60 * 15):
                starttime, endtime = self._info.getNextWackeuptime()
                updated = time.time()
                self._logger.info("Updating the calendar")

            time.sleep(5)

if __name__ == '__main__':
    a = AlarmClock()
    time.sleep(1)
    a.start()
    time.sleep(5)
