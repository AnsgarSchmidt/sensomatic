import os
import sys
import time
import Queue
import threading
import ConfigParser
import paho.mqtt.client as     mqtt
from   influxdb         import InfluxDBClient


class Influx(threading.Thread):

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

        if not self._config.has_section('INFLUX'):
            print "Adding INFLUX part"
            update = True
            self._config.add_section("INFLUX")

        if not self._config.has_option("INFLUX", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("INFLUX", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("INFLUX", "ServerPort"):
            print "No Server Port"
            update = True
            self._config.set("INFLUX", "ServerPort", "8086")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)
                sys.exit(0)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

        self._workingQueue = Queue.Queue()

        self._mqclient = mqtt.Client("Influx", clean_session=True)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)

        self._influx = InfluxDBClient('hal', 8086, 'root', 'root', 'example')
        self._check_db()

    def _check_db(self):
        exists = False

        for e in self._influx.get_list_database():
            if e['name'] == "horizon":
                exists = True

        if exists:
            print "Influx DB does exists"
            self._influx.switch_database("horizon")
            #self._influx.drop_database('horizon')
        else:
            print "Influx DB does not exists, create one"
            self._influx.create_database("horizon")
            self._influx.switch_database("horizon")

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected Influx with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        pass
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        self._workingQueue.put((msg.topic, msg.payload))

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect Influx"

    def _process(self):
        k, v      = self._workingQueue.get()
        keys      = k.split("/")
        json_body = [{"measurement": "", "fields": {"value": 0.0}}]
        json_body[0]['fields']['value'] = float(v)

        if len(keys) == 2 and keys[0] == "ansiroom":

            if keys[1] == "temperature":
                json_body[0]['measurement'] = "ansiroom-temperature"
                self._influx.write_points(json_body)

            if keys[1] == "co2":
                json_body[0]['measurement'] = "ansiroom-co2"
                self._influx.write_points(json_body)

        if len(keys) == 2 and keys[0] == "bathroom":

            if keys[1] == "temperature":
                json_body[0]['measurement'] = "bathroom-temperature"
                self._influx.write_points(json_body)

            if keys[1] == "humidity":
                json_body[0]['measurement'] = "bathroom-humidity"
                self._influx.write_points(json_body)

        if len(keys) == 2 and keys[0] == "livingroom":

            if keys[1] == "temperature":
                json_body[0]['measurement'] = "livingroom-temperature"
                self._influx.write_points(json_body)

            if keys[1] == "humidity":
                json_body[0]['measurement'] = "livingroom-humidity"
                self._influx.write_points(json_body)

        if len(keys) == 3 and keys[0] == "livingroom" and keys[1] == "tank":

            if keys[1] == "watertemp":
                json_body[0]['measurement'] = "tank-temperature"
                self._influx.write_points(json_body)

            if keys[1] == "heater":
                json_body[0]['measurement'] = "tank-heater"
                if float(v) > 0.0:
                    json_body[0]['fields']['value'] = True
                else:
                    json_body[0]['fields']['value'] = False
                self._influx.write_points(json_body)

            if keys[1] == "whitelight":
                json_body[0]['measurement'] = "tank-white"
                self._influx.write_points(json_body)

            if keys[1] == "bluelight":
                json_body[0]['measurement'] = "tank-blue"
                self._influx.write_points(json_body)

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        while True:
            try:
                self._process()
            except Exception as e:
                print ("Error in processing")
                print e


if __name__ == '__main__':
    print "Start"

    i = Influx()
    i.start()

    time.sleep(10)

    print "End"
