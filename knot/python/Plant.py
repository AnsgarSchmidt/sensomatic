import mraa
import time
import xively
import datetime
import threading
import paho.mqtt.client as mqtt

class Plant(threading.Thread):

    PIN_PUMP = 3
    PIN_LED  = 5

    PIN_ENABLE_SOIL  = 4
    PIN_ENABLE_WATER = 6

    PIN_MEASURE_SOIL  = A5
    PIN_MEASURE_WATER = A4

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

        if not self._config.has_section('XIVELY'):
            print "Adding xively part"
            update = True
            self._config.add_section("XIVELY")

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

        self._pump = mraa.Pwm(PIN_PUMP)
        self._pump.period_us(1000)
        self._pump.write(0.0)
        self._pump.enable(True)

        self._led = mraa.Pwm(PIN_LED)
        self._led.period_us(500)
        self._led.write(0.0)
        self._led.enable(True)

        self._enableSoil   = mraa.Gpio(PIN_ENABLE_SOIL)
        self._enableWater  = mraa.Gpio(PIN_ENABLE_WATER)
        self._measureSoil  = mraa.Analog(PIN_MEASURE_SOIL)
        self._measureWater = mraa.Analog(PIN_MEASURE_WATER)

        self.connect()

        self._mqclient = mqtt.Client("plant", clean_session=True)
        self._mqclient.connect("cortex", 1883, 60)
        self._mqclient.on_connect = on_connect
        self._mqclient.on_message = on_message

        self.start()

    def run(self):
        counter = 2
        while True:
            self._mqclient.loop()

    def connect(self):
        self._xively                = xively.XivelyAPIClient(self._config.get("XIVELY","APIKey"))
        self._feed                  = self._xively.feeds.get(self._config.get("XIVELY","feedid"))
        self._datastream_soil       = self._get_datastream("soil")
        self._datastream_waterlevel = self._get_datastream("waterlevel")

    def _get_datastream(self, title):
      try:
        datastream = self._feed.datastreams.get(title)
        return datastream
      except:
        datastream = self._feed.datastreams.create(title)
        return datastream

    def water(self, duration):
        if duration < 10.0:
            self._pump.write(1.0)
            time.sleep(0.3)
            self._pump.write(0.4)
            time.sleep(duration)
            self._pump.write(0.0)

    def led(self, percentage):
        self._led.write(percentage / 100.0)

    def measureSoil(self):
        self._enableSoil.write(True)
        time.sleep(0.5)
        value = 0.0
        for i in range(100):
            value += self._measureSoil.read()
        self._enableSoil.write(False)
        value = value / 100.0
        return value

    def measureWater(self):
        self._enableWater.write(True)
        time.sleep(0.5)
        value = 0.0
        for i in range(100):
            value += self._measureWater.read()
        self._enableWater.write(False)
        value = value / 100.0
        return value

    def isWater(self):
        if self.measureWater() < 0.5:
            return True
        else:
            return False

    def measure(self):
        soil  = self.measureSoil()
        water = self.measureWater()

        try:
            self._datastream_soil.current_value         = soil
            self._datastream_soil.at                    = datetime.datetime.utcnow()
            self._datastream_soil.update()
            self._datastream_waterlevel.current_value   = water
            self._datastream_waterlevel.at              = datetime.datetime.utcnow()
            self._datastream_waterlevel.update()
        except:
            self.connect()

        self._mqclient.publish("plant/spoil", spoil)
        self._mqclient.publish("plant/water", water)

    def on_connect(client, userdata, rc):
        print("Connected with result code "+str(rc))
        client.subscribe("plant/+")

    def on_message(client, userdata, msg):
        print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)
        parts   = msg.topic.split("/")
        channel = parts[2]
        val     = int(msg.payload)

if __name__ == '__main__':
    print "Plant"

    p = Plant()

    while True:
        time.sleep(1000)