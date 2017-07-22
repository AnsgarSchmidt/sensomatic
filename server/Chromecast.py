import os
import sys
import pafy
import time
import Queue
import logging
import threading
import ConfigParser
import pychromecast
import paho.mqtt.client   as     mqtt

class Chromecast(threading.Thread):

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
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._workingQueue           = Queue.Queue()
        self._mqclient               = mqtt.Client("Chromecast", clean_session=True)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.loop_start()
        self._chromecasts            = {}
        self._chromecasts_OK         = False

    def _on_connect(self, client, userdata, rc, msg):
        self._logger.info("Connected Chromecast with result code %s" % rc)
        self._mqclient.subscribe("chromecast/#")

    def _on_message(self, client, userdata, msg):
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        self._logger.error("Disconnect Chromecast")

    def _disconnectAll(self):
        try:
            for i in self._chromecasts:
                i.disconnect()
            self._chromecasts = {}
        except Exception as e:
            self._logger.error(e)
            self._chromecasts = {}

    def _discoverAll(self):
        self._disconnectAll()
        try:
            casts = pychromecast.get_chromecasts(timeout=10)
            for i in casts:
                self._logger.info(i)
                self._chromecasts[i.device.friendly_name] = i
            self._chromecasts_OK = True
        except Exception as e:
            self._chromecasts_OK = False
            self._logger.erro(e)

    def run(self):
        while True:

            if not self._chromecasts_OK:
                self._discoverAll()

            try:
                k, v = self._workingQueue.get()
                keys = k.split("/")
                self._logger.debug(k)
                self._logger.debug(v)

                if keys[1] in self._chromecasts.keys():
                    self._logger.debug("Found device")
                    cast = self._chromecasts[keys[1]]

                    if keys[2] == "playYoutube":
                        self._logger.info("playYoutube")
                        audiostream = pafy.new("https://www.youtube.com/watch?v=" + v).getbestaudio()
                        cast.wait()
                        mc = cast.media_controller
                        mc.play_media(audiostream.url, 'audio/' + audiostream.extension)
                        mc.block_until_active()
                        mc.play()

                    if keys[2] == "playMusicURL":
                        self._logger.info("playMusicURL")
                        cast.wait()
                        # We start one because this can be just a change of media source
                        mc = cast.media_controller
                        mc.play_media(v, 'audio/mpeg')
                        mc.block_until_active()
                        mc.play()
                        time.sleep(5)
                        counter = 0
                        while counter < 5 and cast.status.app_id is None:
                            self._logger.info("retry playMusicURL")
                            mc.play_media(v, 'audio/mpeg')
                            mc.block_until_active()
                            mc.play()
                            time.sleep(5)
                            counter += 1

                    if keys[2] == "volume":
                        self._logger.info("volume")
                        cast.wait()
                        cast.set_volume(float(v))

                    if keys[2] == "stop":
                        self._logger.info("stop")
                        cast.wait()
                        cast.quit_app()

            except Exception as e:
                self._logger.error("Error in processing")
                self._logger.error(e)
                self._chromecasts_OK = False
                self._mqclient.publish(k, v)

if __name__ == '__main__':
    c = Chromecast()
    c.start()
    time.sleep(60)

    #c.playMusicURL('Chromeansi', 'http://inforadio.de/livemp3')
    #time.sleep(1)
    #c.volume('Chromeansi', 0.6)
    #time.sleep(1)
    #c.volume('Chromeansi', 0.1)
    #time.sleep(1)
    #c.stop('Chromeansi')
    #print c.getVolume('Chromeansi')
    #print c.getDisplayName('Chromeansi')
    #c.stop('Chromeansi')
    #c.test('Chromeansi')
    #c.playYoutube('Chromeansi', '0fYL_qiDYf0')
    #c.volume('Chromeansi', 0.6)
