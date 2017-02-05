import os
import time
import ping
import threading
import ConfigParser
import paho.mqtt.client as mqtt

class Pinger(threading.Thread):

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

        if not self._config.has_section('PINGER'):
            print "Adding Pinger part"
            update = True
            self._config.add_section("PINGER")

        if not self._config.has_option("PINGER", "AnsiIP"):
            print "No AnsiAddress Address"
            update = True
            self._config.set("PINGER", "AnsiIP", "192.168.1.10")

        if not self._config.has_option("PINGER", "TiffyIP"):
            print "No Tiffy IP Address"
            update = True
            self._config.set("PINGER", "TiffyIP", "192.168.1.20")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient       = mqtt.Client("Pinger", clean_session=True)
        self._crew           = {"ansi": False, "tiffy": False}

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.loop_start()
        while True:
            a = ping.quiet_ping(self._config.get("PINGER", "AnsiIP"), timeout=1, count=1)
            if a[0] == 0:
                self._mqclient.publish("ansi/wlanPresents", "1")
            else:
                self._mqclient.publish("ansi/wlanPresents", "0")

            t = ping.quiet_ping(self._config.get("PINGER", "TiffyIP"), timeout=1, count=1)
            if t[0] == 0:
                self._mqclient.publish("tiffy/wlanPresents", "1")
            else:
                self._mqclient.publish("tiffy/wlanPresents", "0")

            time.sleep(30)

if __name__ == "__main__":

    p = Pinger()
    p.start()

    time.sleep(100)
