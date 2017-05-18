# Main code copied from https://github.com/GadgetReactor/pyHS100/blob/master/pyHS100/pyHS100.py

# Parts of this code reuse code and concepts by Lubomir Stroetmann from softScheck GmbH
# licensed under the Apache License v 2.0.
# Copy of the Apache License can be found at http://www.apache.org/licenses/LICENSE-2.0
# The code from Lubomir Stroetmann is located at http://github.com/softScheck/tplink-smartplug

import socket
import time
import json
import datetime
import ConfigParser
import threading
import sys
import os
import paho.mqtt.client as mqtt


class HS100(threading.Thread):

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

    def __init__(self, ip, namespace):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient       = mqtt.Client("HS100"+ip, clean_session=True)
        self.ip              = ip
        self.port            = 9999
        self.namespace       = namespace
        self._error_report   = False
        self.model           = self._identify_model()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected HS100"+self.ip+" with result code %s" % rc

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect HS100"+self.ip

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        while True:
            time.sleep(5)
            try:
                rt = self.get_emeter_realtime()
                if rt is not None:
                    self._mqclient.publish(self.namespace + "voltage", rt['voltage']    )
                    self._mqclient.publish(self.namespace + "current", rt['current']    )
                    self._mqclient.publish(self.namespace + "state",   self.get_state() )
            except:
                print "Error connecting HS100:" + self.namespace

    def get_state(self):
        response = self.get_info()
        return response["system"]["get_sysinfo"]["relay_state"]

    def get_info(self):
        return self._send_command('{"system":{"get_sysinfo":{}}}')

    def turn_on(self):
        response = self._send_command('{"system":{"set_relay_state":{"state":1}}}')

        if response["system"]["set_relay_state"]["err_code"] == 0:
            return True

        return False

    def turn_off(self):
        response = self._send_command('{"system":{"set_relay_state":{"state":0}}}')

        if response["system"]["set_relay_state"]["err_code"] == 0:
            return True

        return False

    def get_emeter_realtime(self):
        if self.model == 100:
            return False

        response = self._send_command('{"emeter":{"get_realtime":{}}}')

        if response["emeter"]["get_realtime"]["err_code"] != 0:
            return False

        response["emeter"]["get_realtime"].pop('err_code', None)
        return response["emeter"]["get_realtime"]

    def get_emeter_daily(self, year=datetime.datetime.now().year, month=datetime.datetime.now().month):
        if self.model == 100:
            return False

        response = self._send_command('{"emeter":{"get_daystat":{"month":' + str(month) + ',"year":' + str(year) + '}}}')

        if response["emeter"]["get_daystat"]["err_code"] != 0:
            return False

        data = dict()

        for i, j in enumerate(response["emeter"]["get_daystat"]["day_list"]):
            if j["energy"] > 0:
                data[j["day"]] = j["energy"]

        return data

    def get_emeter_monthly(self, year=datetime.datetime.now().year):
        if self.model == 100:
            return False

        response = self._send_command('{"emeter":{"get_monthstat":{"year":' + str(year) + '}}}')

        if response["emeter"]["get_monthstat"]["err_code"] != 0:
            return False

        data = dict()

        for i, j in enumerate(response["emeter"]["get_monthstat"]["month_list"]):
            if j["energy"] > 0:
                data[j["month"]] = j["energy"]

        return data

    def erase_emeter_stats(self):
        if self.model == 100:
            return False

        response = self._send_command('{"emeter":{"erase_emeter_stat":null}}')

        if response["emeter"]["erase_emeter_stat"]["err_code"] != 0:
            return False
        else:
            return True

    def current_consumption(self):
        if self.model == 100:
            return False

        response = self.get_emeter_realtime()

        return response["power"]

    def _encrypt(self, string):
        """
        Taken from https://raw.githubusercontent.com/softScheck/tplink-smartplug/master/tplink-smartplug.py
        Changes: the return value is encoded in latin-1 in Python 3 and later
        """
        key = 171
        result = "\0\0\0\0"
        for i in string:
            a = key ^ ord(i)
            key = a
            result += chr(a)

        if sys.version_info.major > 2:
            return result.encode('latin-1')

        return result

    def _decrypt(self, string):
        """
        Taken from https://raw.githubusercontent.com/softScheck/tplink-smartplug/master/tplink-smartplug.py
        Changes: the string parameter is decoded from latin-1 in Python 3 and later
        """
        if sys.version_info.major > 2:
            string = string.decode('latin-1')

        key = 171
        result = ""
        for i in string:
            a = key ^ ord(i)
            key = ord(i)
            result += chr(a)

        return result

    def _send_command(self, command):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))
        s.send(self._encrypt(command))
        response = self._decrypt(s.recv(4096)[4:])
        s.shutdown(1)
        s.close()
        return json.loads(response)

    def _identify_model(self):
        sys_info = self.get_info()

        if sys_info["system"]["get_sysinfo"]["model"][:5] == 'HS100':
            model = 100
        elif sys_info["system"]["get_sysinfo"]["model"][:5] == 'HS110':
            model = 110

        return model

if __name__ == '__main__':
    p = HS100("192.168.1.42", "bathroom/washingmachine/")
    p.start()
    time.sleep(23)
    #p.turn_on()
    #print p.current_consumption()
    #print p.get_info()
    #print p.get_emeter_realtime()
    #print p.get_emeter_daily()
    #print p.get_emeter_monthly()
    #p.turn_off()
    #print(p.state())
