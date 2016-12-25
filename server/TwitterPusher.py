import os
import sys
import time
import threading
import ConfigParser
import paho.mqtt.client as     mqtt
from   twitter          import *

class TwitterPusher(threading.Thread):

    def _readConfig(self):
        update = False
        stop = False

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

        if not self._config.has_section('TWITTER'):
            print "Adding Twitter part"
            update = True
            self._config.add_section("TWITTER")

        if not self._config.has_option("TWITTER", "ConsumerKey"):
            print "No Twitter Consumer Key"
            update = True
            self._config.set("TWITTER", "ConsumerKey", "<ConsumerKey>")

        if not self._config.has_option("TWITTER", "ConsumerSecret"):
            print "No Twitter ConsumerSecret"
            update = True
            self._config.set("TWITTER", "ConsumerSecret", "<ConsumerSecret>")

        if not self._config.has_option("TWITTER", "AccessToken"):
            print "No Twitter AccessToken"
            update = True
            self._config.set("TWITTER", "AccessToken", "<AccessToken>")

        if not self._config.has_option("TWITTER", "AccessTokenSecret"):
            print "No Twitter AccessTokenSecret"
            update = True
            self._config.set("TWITTER", "AccessTokenSecret", "<AccessTokenSecret>")

        if not self._config.has_section('CHARTS'):
            print "Adding Charts part"
            update = True
            self._config.add_section("CHARTS")

        if not self._config.has_option("CHARTS", "ChartsDir"):
            print "No ChartsDir name"
            update = True
            stop = True
            self._config.set("CHARTS", "ChartsDir", "<Chartsdir>")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

        if stop:
            print "Please check config file"
            sys.exit(0)

    def _checkChartFolder(self):
        if not os.path.isdir(self._chartDir):
            print "Creating chartsDir"
            os.makedirs(self._chartDir)

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._mqclient       = mqtt.Client("TwitterPusher", clean_session=True)
        self._oauth          = OAuth(self._config.get("TWITTER", "accesstoken"),
                                     self._config.get("TWITTER", "accesstokensecret"),
                                     self._config.get("TWITTER", "consumerkey"),
                                     self._config.get("TWITTER", "consumersecret")
                                    )
        self._twitter        = Twitter(                             auth=self._oauth)
        self._twittermedia   = Twitter(domain='upload.twitter.com', auth=self._oauth)
        self._chartDir        = self._config.get("CHARTS", "ChartsDir")
        self._checkChartFolder()

    def _on_connect(self, client, userdata, rc, msg):
        print "Connected TwitterPusher with result code %s" % rc
        self._mqclient.subscribe("twitter/#")

    def _send_picture(self, pictureFileName, text):
        try:
            with open(self._chartDir + "/" + pictureFileName, "rb") as imagefile:
                imagedata = imagefile.read()
            uploadresult = self._twittermedia.media.upload(media=imagedata)
            results      = self._twitter.statuses.update(status=text, media_ids=uploadresult["media_id_string"])
            print results['user']['statuses_count']
        except:
            print "Unexpected error:", sys.exc_info()[0]

    def _send_uploaded_picture(self, id, text):
        try:
            results      = self._twitter.statuses.update(status=text, media_ids=id)
            print results['user']['statuses_count']
        except:
            print "Unexpected error:", sys.exc_info()[0]

    def _send_text(self, text):
        try:
            print "Tweeting %s" % text
            results = self._twitter.statuses.update(status=text)
            print results['user']['statuses_count']
        except:
            pass

    def _on_message(self, client, userdata, msg):
        #print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        try:
            keys = msg.topic.split("/")
            if keys[1] == "text":
                self._send_text(msg.payload)
            if keys[1] == "picture":
                self._send_picture(keys[2], msg.payload)
            if keys[1] == "uploaded":
                self._send_uploaded_picture(keys[2], msg.payload)
        except:
            pass

    def _on_disconnect(self, client, userdata, msg):
        print "Disconnect TwitterPusher"

    def run(self):
        self._mqclient.connect(self._config.get("MQTT", "ServerAddress"), self._config.get("MQTT", "ServerPort"), 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_forever()

if __name__ == '__main__':
    print "Start"
    t = TwitterPusher()
    t.start()
    time.sleep(23)
    print "End"