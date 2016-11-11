import os
import datetime
import subprocess
import time
import ConfigParser
import sys
import Queue
import threading
import paho.mqtt.client   as     mqtt

#bluetoothctl
#scan on
#<Wait for the thermostat to be found, which looks like this: [NEW] Device 00:11:22:33:44:55 CC-RT-BLE>
#scan off
#<Set the thermostat to pairing mode.>
#pair <MAC>
#trust <MAC>
#disconnect <MAC>
#exit

# https://raw.githubusercontent.com/mpex/EQ3-Thermostat/master/eq3_control.py

class EQ3Thermostat(threading.Thread):

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

        if not self._config.has_section('EQ3'):
            print "Adding EQ3 part"
            update = True
            self._config.add_section("EQ3")

        if not self._config.has_option("EQ3", "Address"):
            print "No Address"
            update = True
            self._config.set("EQ3", "Address", "<MACAddress>")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit()

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir                = os.path.expanduser("~/.sensomatic")
        self._configFileName         = self._homeDir + '/config.ini'
        self._humidityFileName       = self._homeDir + '/humidity.txt'
        self._temperatureFileName    = self._homeDir + '/temperature.txt'
        self._config                 = ConfigParser.ConfigParser()
        self._readConfig()
        self._address                = self._config.get("EQ3", "Address")
        self._locked                 = False
        self._temperature            = 0
        self._workingQueue           = Queue.Queue()
        self._mqclient               = mqtt.Client("EQ3", clean_session=True)
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        self._update()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected EQ3 with result code %s" % rc
        self._mqclient.subscribe("ansiroom/settemp")

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect EQ3"

    def run(self):
        while True:
            try:
                self._process()
            except:
                pass

    def _process(self):
        k, v = self._workingQueue.get()
        keys = k.split("/")
        print "Setting temperature to %f" % float(v)
        self.set_temperature(float(v))

    def _update(self):
        """Reads the current temperature from the thermostat. We need to kill
        the gatttool process as the --listen option puts it into an infinite
        loop."""
        p = subprocess.Popen(["timeout", "-s", "INT", "5", "gatttool", "-b",
                              self._address, "--char-write-req", "-a", "0x0411",
                              "-n", "03", "--listen"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err     = p.communicate()
        value_string = out.decode("utf-8")

        if "Notification handle" in value_string:
            value_string_splt = value_string.split()
            temperature       = value_string_splt[-1]
            locked            = value_string_splt[-4]
            try:
                subprocess.Popen.kill(p)
            except:
                pass

            if locked == "20":
                self.locked = True
            elif locked == "00":
                self.locked = False
            else:
                pass
                #print("Could not read lockstate of {}".format(self.address))

            try:
                self.temperature = int(temperature, 16) / 2
            except Exception as e:
                print("Getting temperature of {} failed {}".format(self.address, e))

    def activate_boostmode(self):
        """Boostmode fully opens the thermostat for 300sec."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "4501"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def deactivate_boostmode(self):
        """Use only to stop boostmode before 300sec."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "4500"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_automatic_mode(self):
        """Put thermostat in automatic mode."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "4000"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_manual_mode(self):
        """Put thermostat in manual mode."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "4040"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_eco_mode(self):
        """Put thermostat in eco mode."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "4080"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def lock_thermostat(self):
        """Locks the thermostat for manual use."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "8001"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def unlock_thermostat(self):
        """Unlocks the thermostat for manual use."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "8000"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_temperature(self, temperature):
        """Transform the temperature in celcius to make it readable to the thermostat."""
        temperature = hex(int(2 * float(temperature)))[2:]
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "41{}".format(temperature)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Block for 3 secs to let the thermostat adjust the temperature
        time.sleep(3)

    def get_temperature(self):
        return self._temperature

    def set_temperature_offset(self, offset):
        """Untested."""
        temperature = hex(int(2 * float(offset) + 7))[2:]
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "13{}".format(temperature)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_day(self):
        """Puts thermostat into day mode (sun icon)."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "43"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_night(self):
        """Puts thermostat into night mode (moon icon)."""
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "44"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_day_night(self, night, day):
        """Sets comfort temperature for day and night."""
        day = hex(int(2 * float(day)))[2:]
        night = hex(int(2 * float(night)))[2:]
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "11{}{}".format(day, night)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_windows_open(self, temperature, duration_min):
        """Untested."""
        temperature = hex(int(2 * float(temperature)))[2:]
        duration_min = hex(int(duration_min / 5.0))[2:]
        p = subprocess.Popen(["gatttool", "-b", self._address, "--char-write-req",
                              "-a", "0x0411", "-n", "11{}{}".format(temperature, duration_min)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def set_time(self, datetimeobj = datetime.datetime.now()):
        """Takes a datetimeobj (like datetime.datetime.now()) and sets the time
        in the thermostat."""
        command_prefix = "03"
        year           = "{:02X}".format(datetimeobj.year % 100)
        month          = "{:02X}".format(datetimeobj.month)
        day            = "{:02X}".format(datetimeobj.day)
        hour           = "{:02X}".format(datetimeobj.hour)
        minute         = "{:02X}".format(datetimeobj.minute)
        second         = "{:02X}".format(datetimeobj.second)
        control_string = "{}{}{}{}{}{}{}".format(command_prefix, year, month, day, hour, minute, second)
        p              = subprocess.Popen(["gatttool", "-b", self.address, "--char-write-req",
                                           "-a", "0x0411", "-n", control_string],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Block for 3 secs to let the thermostat adjust the settings
        time.sleep(3)

if __name__ == '__main__':
    h = EQ3Thermostat()
    h.start()
    time.sleep(256)
