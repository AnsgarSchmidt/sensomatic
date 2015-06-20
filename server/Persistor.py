import os
import redis
import threading
import ConfigParser
import paho.mqtt.client as mqtt

class Persistor(threading.Thread):

    def readConfig(self):
        update = False

        if not os.path.isdir(self.homeDir):
            print "Creating homeDir"
            os.makedirs(self.homeDir)

        if os.path.isfile(self.configFileName):
            self.config.read(self.configFileName)
        else:
            print "Config file not found"
            update = True

        if not self.config.has_section('MQTT'):
            print "Adding MQTT part"
            update = True
            self.config.add_section("MQTT")

        if not self.config.has_option("MQTT", "ServerAddress"):
            print "No Server Address"
            update = True
            self.config.set("MQTT", "ServerAddress", "<ServerAddress>")

        if not self.config.has_option("MQTT", "ServerPort"):
            print "No Server Port"
            update = True
            self.config.set("MQTT", "ServerPort", "<ServerPort>")

        if not self.config.has_section('REDIS'):
            print "Adding Redis part"
            update = True
            self.config.add_section("REDIS")

        if not self.config.has_option("REDIS", "ServerAddress"):
            print "No Server Address"
            update = True
            self.config.set("REDIS", "ServerAddress", "<ServerAddress>")

        if not self.config.has_option("REDIS", "ServerPort"):
            print "No Server Port"
            update = True
            self.config.set("REDIS", "ServerPort", "<ServerPort>")

        if update:
            with open(self.configFileName, 'w') as f:
                self.config.write(f)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.homeDir        = os.path.expanduser("~/.sensomatic")
        self.configFileName = self.homeDir + '/config.ini'
        self.config         = ConfigParser.ConfigParser()
        self.readConfig()


    def run(self):
        pass






if __name__ == '__main__':
    print "Start"

    p = Persistor()
    p.start()