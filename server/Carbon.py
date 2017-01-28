import os
import time
import socket
import ConfigParser

class Carbon():

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

        if not self._config.has_section('CARBON'):
            print "Adding CARBON part"
            update = True
            self._config.add_section("CARBON")

        if not self._config.has_option("CARBON", "Address"):
            print "No Server Address"
            update = True
            self._config.set("CARBON", "Address", "<ServerAddress>")

        if not self._config.has_option("CARBON", "Port"):
            print "No Port"
            update = True
            self._config.set("CARBON", "Port", "2003")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._socket         = socket.socket()
        self._connect()

    def _connect(self):
        self._socket.connect((self._config.get("CARBON", "Address"), int(self._config.get("CARBON", "Port"))))
        print "Connected"

    def sendData(self, topic, value):
        try:
            message = '%s %s %d\n' % (topic, value, time.time())
            self._socket.sendall(message)
        except Exception as e:
            print e
            self._connect()

if __name__ == '__main__':
    print "Test"
    c = Carbon()
    c.sendData("ansiroom.bloedsinn1" , 32.5)
    while True:
        c.sendData("ansiroom.bloedsinn2", 133)
        time.sleep(1)
