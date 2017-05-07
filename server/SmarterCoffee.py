import os
import sys
import time
import Queue
import socket
import threading
import ConfigParser
import paho.mqtt.client as     mqtt
from   array            import array

#based on https://github.com/jkellerer/fhem-smarter-coffee/blob/master/fhem/FHEM/98_SmarterCoffee.pm

class SmartCoffee(threading.Thread):

    returnMessageType = {
        '0x0': "Ok",
        '0x1': "Ok: Brewing in progress",
        '0x4': "Ok: stopped",
        '0x5': "Error: No Carafe",
        '0x6': "Error: No Water",
        '0x69': "Invalid Command"
    }

    waterLevelMessageType = {
        0: "Not enough water",
        1: "Low",
        2: "Half",
        3: "Full",
    }

    strengthMessageType = {
        '0x0': "weak",
        '0x1': "medium",
        '0x2': "strong",
    }

    def _readConfig(self):

        if self._configMTime != os.stat(self._configFileName).st_mtime:

            print "Reread config file for SmarterCoffee"
            self._configMTime = os.stat(self._configFileName).st_mtime
            update = False
            stop   = False

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

            if not self._config.has_section('COFFEE'):
                print "Adding Coffee part"
                update = True
                self._config.add_section("COFFEE")

            if not self._config.has_option("COFFEE", "Address"):
                print "No coffee address"
                update = True
                self._config.set("COFFEE", "Address", "192.168.0.210")

            if not self._config.has_option("COFFEE", "Enabled"):
                print "No enablement"
                update = True
                self._config.set("COFFEE", "Enabled", True)

            if not self._config.has_option("COFFEE", "Cups"):
                print "No cups"
                update = True
                self._config.set("COFFEE", "Cups", 5)

            if not self._config.has_option("COFFEE", "Grinding"):
                print "No grinding"
                update = True
                self._config.set("COFFEE", "Grinding", True)

            if not self._config.has_option("COFFEE", "Strength"):
                print "No strength"
                update = True
                self._config.set("COFFEE", "Strength", 2)

            if not self._config.has_option("COFFEE", "HotPlateTime"):
                print "No Hotplatetime"
                update = True
                self._config.set("COFFEE", "HotPlateTime", 23)

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

            if stop:
                print "Please check config file"
                sys.exit(0)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._workingQueue    = Queue.Queue()
        self._homeDir         = os.path.expanduser("~/.sensomatic")
        self._configFileName  = self._homeDir + '/config.ini'
        self._configMTime     = 0
        self._config          = ConfigParser.ConfigParser()
        self._readConfig()
        self._reconnect()
        self._mqclient        = mqtt.Client("SmarterCoffee", clean_session=True)

    def _reconnect(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._config.get("COFFEE", "Address"), 2081))
        except socket.error:
            print "Failed to reconnect to socket"

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected MQTT Carbon with result code %s" % rc
        self._mqclient.subscribe("coffee/brew_wakeup_coffee")

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        if msg.topic == "coffee/brew_wakeup_coffee":
            self.brew_wakeup()

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect MQTTRulez"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()

        while True:
            try:
                if not self._workingQueue.empty():
                    self._socket.send(self._workingQueue.get().decode('hex'))
                    print "sending command to coffee machine"

                rhex = self._socket.recv(50)
                a = array("B", rhex)
                hexval = map(hex, a)

                if hexval[0] == "0x3":
                    print "Response to command" + str(SmartCoffee.returnMessageType[hexval[1]])
                elif hexval[0] == "0x47":
                    print "History"
                elif hexval[0] == "0x49":
                    cups     = int(hexval[1], 16)
                    strength = int(hexval[2], 16)
                    grinder  = int(hexval[3], 16)
                    hotplate = int(hexval[4], 16)
                    print "Defaults:" + str([cups, strength, grinder, hotplate])
                elif hexval[0] == "0x4d":
                    print "Carafe required:" + str(hexval[1] == "0x0")
                elif hexval[0] == "0x50":
                    print "Single cup:" + str(hexval[1] == "0x0")
                elif hexval[0] == "0x65":
                    print "Firmware:" + str(hexval[2])
                elif hexval[0] == "0x32":
                    status        = int(hexval[1], 16)
                    waterlevel    = SmartCoffee.waterLevelMessageType[int(hexval[2], 16) & 0b00001111]
                    strength      = SmartCoffee.strengthMessageType[hexval[4]]
                    cups = int(hexval[5], 16) & 0b00001111
                    self._mqclient.publish("coffee/waterlevel", waterlevel)
                    self._mqclient.publish("coffee/strength", strength)
                    self._mqclient.publish("coffee/cups", cups)

                    if status & 0b00000001:
                        self._mqclient.publish("coffee/carafe", 1)
                    else:
                        self._mqclient.publish("coffee/carafe", 0)

                    if status & 0b00000010:
                        self._mqclient.publish("coffee/grinder_activated", 1)
                    else:
                        self._mqclient.publish("coffee/grinder_activated", 0)

                    if status & 0b00000100:
                        self._mqclient.publish("coffee/ready", 1)
                    else:
                        self._mqclient.publish("coffee/ready", 0)

                    if status & 0b00001000:
                        self._mqclient.publish("coffee/grinding", 1)
                    else:
                        self._mqclient.publish("coffee/grinding", 0)

                    if status & 0b00010000:
                        self._mqclient.publish("coffee/brewing", 1)
                    else:
                        self._mqclient.publish("coffee/brewing", 0)

                    if status & 0b00100000:
                        self._mqclient.publish("coffee/idle_heating", 1)
                    else:
                        self._mqclient.publish("coffee/idle_heating", 0)

                    if status & 0b01000000:
                        self._mqclient.publish("coffee/hotplate", 1)
                    else:
                        self._mqclient.publish("coffee/hotplate", 0)

                    if status & 0b10000000:
                        print "No idea"

                else:
                    print "Unknown"

            except Exception as e:
                print "error"
                print e
                time.sleep(60)
                self._reconnect()

    def reset(self):
        self._workingQueue.put("107e")

    def brew(self):
        self._workingQueue.put("377e")

    def brew_wakeup(self):
        if self._config.getboolean("COFFEE", "Enabled"):
            print "Brewing wakeup coffee"
            cups         = self._config.getint("COFFEE", "Cups")
            strength     = self._config.getint("COFFEE", "Strength")
            grinding     = self._config.getboolean("COFFEE", "Grinding")
            hotplatetime = self._config.getint("COFFEE", "HotPlateTime")
            self.brew_with_settings(cups, strength, grinding, hotplatetime)
        else:
            print "Brewing disabled"

    def brew_with_settings(self, cups, strength, grinding, hotplatetime):
        self._workingQueue.put("33" + self._prepare_parameter(cups, strength, grinding, hotplatetime) + "7e")

    def set_defaults(self, cups, strength, grinding, hotplatetime):
        self._workingQueue.put("38" + self._prepare_parameter(cups, strength, grinding, hotplatetime) + "7e")

    def toggle_grind(self):
        self._workingQueue.put("3c7e")

    def set_strength(self, strength):
        if strength >= 0 and strength <= 2:
            val = "35%0.2X7e" % strength
        else:
            print "Error: coffee strength must be a value between 0 - 2 autosetting 0"
            val = "35007e"
        self._workingQueue.put(val)

    def set_cups(self, cups):
        if cups <= 12 and cups >= 1:
            val = "36%0.2X7e" % cups
        else:
            print "Error: coffee cups must be a value between 1 - 12 autosetting 1 cup"
            val = "36017e"
        self._workingQueue.put(val)

    def get_default(self):
        self._workingQueue.put("487e")

    def stop(self):
        self._workingQueue.put("347e")

    def hotplate_on_for_minutes(self, minutes):
        if minutes < 5:
            print "Error: Time must be minimum 5. Autosetting 5min"
            val = "3e057e"
        else:
            val = "3e%0.2X7e" % minutes
        self._workingQueue.put(val)

    def hotplate_off(self):
        self._workingQueue.put("4a7e")

    def info(self):
        self._workingQueue.put("647e")

    def history(self):
        self._workingQueue.put("467e")

    def is_carfe_required(self):
        self._workingQueue.put("4c7e")

    def is_cups_single_status(self):
        self._workingQueue.put("4f7e")

    def _prepare_parameter(self, cups, strength, grinding, hotplatetime):
        cupsHex     = ""
        strenghtHex = ""
        grindHex    = ""
        hotPlateHex = ""

        if cups <= 12 and cups >= 1:
            cupsHex = "%0.2X" % cups
        else:
            print "Error: coffee cups must be a value between 1 - 12 autosetting 1 cup"
            cupsHex = "01"

        if strength >= 0 and strength <= 2:
            strengthHex = "%0.2X" % strength
        else:
            print "Error: coffee strength must be a value between 0 - 2 autosetting 0"
            strengthHex = "00"

        if grinding == 1:
            grindHex = "01"
        else:
            grindHex = "00"

        if hotplatetime < 5:
            print "Error: Time must be minimum 5. Autosetting 5min"
            hotPlateHex = "05"
        else:
            hotPlateHex = "%0.2X" % hotplatetime

        finalHex = cupsHex + strengthHex + hotPlateHex + grindHex
        return finalHex

if __name__ == '__main__':
    print "Test"
    c = SmartCoffee()
    c.start()
    time.sleep(300)
