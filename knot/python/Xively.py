import os
import time
import xively
import ConfigParser
import datetime
import subprocess
import threading

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
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._connect()
        self.start()

    def run(self):
        while True:
            self._updateInternal()
            self._updateValue()
            time.sleep(30)

    def _connect(self):
        self._xively                = xively.XivelyAPIClient(self._config.get("XIVELY","APIKey"))
        self._feed                  = self._xively.feeds.get(self._config.get("XIVELY","feedid"))
        self._datastream_room_temp  = self._get_datastream("room_temp")
        self._datastream_humidity   = self._get_datastream("humidity")
        self._datastream_cpu_temp   = self._get_datastream("cpu_temp")
        self._datastream_gpu_temp   = self._get_datastream("gpu_temp")
        self._datastream_load_level = self._get_datastream("load_level")
        self._datastreams           = [self._datastream_room_temp,
                                       self._datastream_humidity,
                                       self._datastream_cpu_temp,
                                       self._datastream_gpu_temp,
                                       self._datastream_load_level
                                      ]
    def _diconnect(self):
        self._mqclient.disconnect()

    def _get_datastream(self, title):
      try:
        datastream = self._feed.datastreams.get(title)
        return datastream
      except:
        datastream = self._feed.datastreams.create(title)
        return datastream

    def _updateValue(self):
        try:
            for d in self._datastreams:
                d.update()
        except:
            self._connect()

    def setRoomTemp(self, temp):
        self._datastream_room_temp.current_value  = temp
        self._datastream_room_temp.at             = datetime.datetime.utcnow()

    def setHumidity(self, hum):
        self._datastream_humidity.current_value   = hum
        self._datastream_humidity.at              = datetime.datetime.utcnow()

    def _updateInternal(self):
        self._datastream_load_level.current_value = subprocess.check_output(["awk '{print $1}' /proc/loadavg"], shell=True)
        self._datastream_load_level.at            = datetime.datetime.utcnow()
        cputemp                                   = int(subprocess.check_output(["awk '{print $1}' /sys/class/thermal/thermal_zone0/temp"], shell=True))
        self._datastream_cpu_temp.current_value   = cputemp / 1000.0
        self._datastream_cpu_temp.at              = datetime.datetime.utcnow()
        gpuTempString                             = subprocess.check_output(["/opt/vc/bin/vcgencmd measure_temp"], shell=True)
        self._datastream_gpu_temp.current_value   = float(gpuTempString[5:][:-3])
        self._datastream_gpu_temp.at              = datetime.datetime.utcnow()

if __name__ == '__main__':
    print "Start"

    x = Xively()
    x.setRoomTemp(12.2)
    x.setHumidity(22.5)

    time.sleep(10)

    print "End"