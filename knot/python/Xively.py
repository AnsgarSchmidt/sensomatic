import os
import xively
import threading
import ConfigParser
import paho.mqtt.client as mqtt
import time

class Xively(threading.Thread):

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

        if not self._config.has_section('XIVELY'):
            print "Adding xively part"
            update = True
            self._config.add_section("XIVELY")

        if not self._config.has_option("XIVELY", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("XIVELY", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("XIVELY", "FeedID"):
            print "No FeedID"
            update = True
            self._config.set("XIVELY", "FeedID", "<FeedID>")

        if not self._config.has_option("XIVELY", "APIKey"):
            print "No APIKey"
            update = True
            self._config.set("XIVELY", "APIKey", "<APIKey>")

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

        self._mqclient  = mqtt.Client("Xively", clean_session=True)
        self._xively    = xively.XivelyAPIClient(self._config.get("XIVELY","APIKey"))
        self._feed_temp = api.feeds.get(FEED_ID)

    def get_datastream(feed, name):
      try:
        datastream = feed.datastreams.get(name)
        return datastream
      except:
        datastream = feed.datastreams.create(name)
        return datastream

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected with result code %s" % rc
        self._mqclient.subscribe("#")

    def _on_message(self, client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT","ServerAddress"), self._config.get("MQTT","ServerPort"), 60)
        self._mqclient.on_connect = self._on_connect
        self._mqclient.on_message = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_forever()

if __name__ == '__main__':
    print "Start"

    x = Xively()
    x.start()

    time.sleep(10)

    print "End"