import os
import time
import telepot
import ConfigParser
import paho.mqtt.client as mqtt

class Telegram():

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

    def __init__(self):
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient               = mqtt.Client("telegram", clean_session=True)
        self._mqclient.connect("cortex", 1883, 60)
        self._mqclient.loop_start()
        self._bot                    = telepot.Bot(self._config.get("TELEGRAM", "Key"))
        self._bot.message_loop(self._handle)
        #print self._bot.getMe()
        self.sendMessage('Start Telegram Bot')

    def _handle(self, msg):
        #print msg
        uID    = msg['from']['id']
        uName  = msg['from']['username']
        uFName = msg['from']['first_name']
        text   = msg['text']
        if uID in self._members:
            self._bot.sendMessage(uID, 'Hey ' + uFName)
            if text == "help":
                self._bot.sendMessage(uID, "I can deal with:\nhelp\nlight ansi\nlight kitchen")
            if text == "light ansi":
                self._bot.sendMessage(uID, "I switch the light in Ansi's room")
                self._mqclient.publish("ansiroom/light/main", "TOGGLE")
            if text == "light kitchen":
                self._bot.sendMessage(uID, "I switch the light in the kitchen room")
                self._mqclient.publish("kitchen/light/main", "TOGGLE")
            if text == "light table":
                self._bot.sendMessage(uID, "I switch the light at the table")
                self._mqclient.publish("hackingroom/light/main", "TOGGLE")
            if text == "light livingroom":
                self._bot.sendMessage(uID, "I switch the light in the living room")
                self._mqclient.publish("livingroom/light/main", "TOGGLE")
            if text == "light tiffy":
                self._bot.sendMessage(uID, "I switch the light in Tiffy's room")
                self._mqclient.publish("tiffyroom/light/main", "TOGGLE")
            if text == "light bathroom":
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

if __name__ == "__main__":
    t = Telegram()
    time.sleep(3)
    t.sendMessage("Hallo Welt")
    time.sleep(42)