import os
import time
import redis
import TM1638
import datetime
import threading
import ConfigParser

DIO = 17
CLK = 27
STB = 22

class LEDKey(threading.Thread):

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
        self.tm = TM1638.TM1638(DIO, CLK, STB)
        self.tm.enable(7)
        for i in range(8):
            self.tm.set_segment(i,8,True)
            self.tm.set_led(i,True)
        time.sleep(1)
        for i in range(8):
            self.tm.set_segment(i,10,False)
            self.tm.set_led(i,False)
        self.tm.disable()
        self.mode = 'nix'
        self._redis = redis.StrictRedis(host=self._config.get("REDIS", "ServerAddress"),
                                        port=self._config.get("REDIS", "ServerPort"), db=0)

    def setMode(self, mode):
        self.mode = mode
        self.tm.enable(7)

    def run(self):
        while True:

            try:
                # Display
                if self.mode == 'timetemp':
                    now = datetime.datetime.now()
                    temp = 88
                    hum  = 00
                    if self._redis.exists("outside/temperature"):
                        temp = float(self._redis.get("outside/feelslike"))
                    if self._redis.exists("outside/humidity"):
                        hum = float(self._redis.get("outside/humidity"))
                    s = "%02d%02d%02d%02d" % (now.hour, now.minute, temp, hum)
                    self.tm.set_text(s)

                # LED 0 -> Heater Tank
                if self._redis.exists("livingroom/tank/heater"):
                    heater = float(self._redis.get("livingroom/tank/heater"))
                    if heater == 1.0:
                        self.tm.set_led(0, 1)
                    else:
                        self.tm.set_led(0, 0)

                # LED 1 -> Heater Waterlevel
                if self._redis.exists("livingroom/tank/waterlevel"):
                    heater = float(self._redis.get("livingroom/tank/waterlevel"))
                    if heater == 1.0:
                        self.tm.set_led(1, 1)
                    else:
                        self.tm.set_led(1, 0)

                # LED 2 -> Heater Whitelight
                if self._redis.exists("livingroom/tank/whitelight"):
                    whitelight = float(self._redis.get("livingroom/tank/whitelight"))
                    if whitelight > 0.0:
                        self.tm.set_led(2, 1)
                    else:
                        self.tm.set_led(2, 0)

                # LED 3 -> Heater Whitelight
                if self._redis.exists("livingroom/tank/bluelight"):
                    bluelight = float(self._redis.get("livingroom/tank/bluelight"))
                    if bluelight > 0.0:
                        self.tm.set_led(3, 1)
                    else:
                        self.tm.set_led(3, 0)

                # LED 4 -> Ansi here
                if self._redis.exists("ansi/wlanPresents"):
                    ansi = int(self._redis.get("ansi/wlanPresents"))
                    if ansi == 1:
                        self.tm.set_led(4, 1)
                    else:
                        self.tm.set_led(4, 0)

                # LED 5 -> Tiffy here
                if self._redis.exists("tiffy/wlanPresents"):
                    tiffy = int(self._redis.get("tiffy/wlanPresents"))
                    if tiffy == 1:
                        self.tm.set_led(5, 1)
                    else:
                        self.tm.set_led(5, 0)
            except Exception as e:
                print e
            time.sleep(1)

if __name__ == "__main__":
    l = LEDKey()
    l.start()
    l.setMode("timetemp")
    while True:
        time.sleep(100)
