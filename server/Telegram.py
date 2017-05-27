import os
import sys
import time
import Queue
import telepot
import threading
import ConfigParser
import paho.mqtt.client as mqtt


class Telegram(threading.Thread):

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

        if not self._config.has_section('TELEGRAM'):
            print "Adding Telegram part"
            update = True
            self._config.add_section("TELEGRAM")

        if not self._config.has_option("TELEGRAM", "Key"):
            print "No Telegram Key"
            update = True
            self._config.set("TELEGRAM", "Key", "<Key>")

        if not self._config.has_option("TELEGRAM", "Members"):
            print "No Members"
            update = True
            self._config.set("TELEGRAM", "Members", "<1,2,3,4>")

        self._members = []
        for i in self._config.get("TELEGRAM", "Members").split(","):
            self._members.append(int(i))

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit(1)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient               = mqtt.Client("telegram", clean_session=True)
        self._bot                    = telepot.Bot(self._config.get("TELEGRAM", "Key"))
        self._workingQueue           = Queue.Queue()

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        self._bot.message_loop(self._handle)
        #print self._bot.getMe()
        self.sendMessage('Start Telegram Bot')
        while True:
            try:
                self._process()
            except Exception as e:
                print e

    def _handle(self, msg):
        #print msg
        uID    = msg['from']['id']
        uName  = msg['from']['username']
        uFName = msg['from']['first_name']
        text   = msg['text']

        if uID in self._members:
            self._bot.sendMessage(uID, 'Hey ' + uFName)
            if text == "help":
                self._bot.sendMessage(uID, "I can deal with:\nhelp\nlight ansi\nlight kitchen\nlight table\nlight living\nlight tiffy\nlight bath")
            if text == "light ansi":
                self._bot.sendMessage(uID, "I switch the light in Ansi's room")
                self._mqclient.publish("ansiroom/light/main", "TOGGLE")
            if text == "light kitchen":
                self._bot.sendMessage(uID, "I switch the light in the kitchen room")
                self._mqclient.publish("kitchen/light/main", "TOGGLE")
            if text == "light table":
                self._bot.sendMessage(uID, "I switch the light at the table")
                self._mqclient.publish("hackingroom/light/main", "TOGGLE")
            if text == "light living":
                self._bot.sendMessage(uID, "I switch the light in the living room")
                self._mqclient.publish("livingroom/light/main", "TOGGLE")
            if text == "light tiffy":
                self._bot.sendMessage(uID, "I switch the light in Tiffy's room")
                self._mqclient.publish("tiffyroom/light/main", "TOGGLE")
            if text == "light bath":
                self._bot.sendMessage(uID, "I switch the light in the bath")
                self._mqclient.publish("bathroom/light/main", "TOGGLE")
        else:
            self._bot.sendMessage(uID, "Sorry %s you are not part of the USS Horizon Crew." % uFName)

    def sendMessage(self, msg):
        try:
            for m in self._members:
                self._bot.sendMessage(m, msg)
        except Exception as e:
            print e

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Rulez with result code %s" % rc
        self._mqclient.subscribe("telegram")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def _process(self):
        k, v = self._workingQueue.get()
        keys = k.split("/")
        if keys[0] == "telegram":
            self.sendMessage(v)

if __name__ == "__main__":
    t = Telegram()
    t.start()
    time.sleep(42)
