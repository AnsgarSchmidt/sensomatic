import os
import time
import Queue
import random
import threading
import ConfigParser
import paho.mqtt.client as mqtt
from   watson_developer_cloud import TextToSpeechV1
from   subprocess             import call


class Tts(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(False)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._tts            = TextToSpeechV1(username=self._config.get('TTS', 'AuthName'),
                                              password=self._config.get('TTS', 'AuthSecret'),
                                              x_watson_learning_opt_out=False)  # Lets learn from our nonsense
        self._mqclient       = mqtt.Client("TTS-%s" % self._config.get("ROOM", "Name"), clean_session=True)
        self._workingQueue   = Queue.Queue()

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

        if not self._config.has_section('TTS'):
            print "Adding TTS part"
            update = True
            self._config.add_section("TTS")

        if not self._config.has_option("TTS", "AuthName"):
            print "No Server AuthName"
            update = True
            self._config.set("TTS", "AuthName", "AuthName")

        if not self._config.has_option("TTS", "AuthSecret"):
            print "No Server AuthSecret"
            update = True
            self._config.set("TTS", "AuthSecret", "<AuthSecret>")

        if not self._config.has_option("TTS", "Voice"):
            print "No Server Voice"
            update = True
            self._config.set("TTS", "Voice", "VoiceEnUsMichael")

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

        if not self._config.has_section('ROOM'):
            print "Adding ROOM part"
            update = True
            self._config.add_section("ROOM")

        if not self._config.has_option("ROOM", "Name"):
            print "No Room Name"
            update = True
            self._config.set("ROOM", "Name", "Sonnendeck")

        if not self._config.has_option("ROOM", "Volume"):
            print "No Room Volume"
            update = True
            self._config.set("ROOM", "Volume", 1.0)

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                os.exit(1)

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT TTS with result code %s" % rc
        self._mqclient.subscribe("%s/ttsout" % self._config.get("ROOM", "Name"))
        print "Subscribed to:%s/ttsout" % self._config.get("ROOM", "Name")

    def _on_message(self, client, userdata, msg):
        # print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put(msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTT TTS"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()

        while True:
            try:
                text = self._workingQueue.get()
                print "Texting:%s" % text
                filename = "/tmp/%i-%d.wav" % (int(time.time()), random.randint(0, 9999999999))
                with open(filename, 'w') as f:
                    f.write(self._tts.synthesize(text, accept='audio/wav', voice=self._config.get('TTS', 'Voice')))
                    call(["play", "-v", "%f" % self._config.getfloat('ROOM', 'Volume'), filename])
                    os.remove(filename)
            except Exception as e:
                print "Error in mainloop"
                print e
                pass

if __name__ == '__main__':
    t = Tts()
    t.start()
