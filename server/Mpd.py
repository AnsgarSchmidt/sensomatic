import mpd
import os
import random
import ConfigParser

class MpdServer():

    def __init__(self, serverName, serverAddress, serverPort=6600):
        self._serverName = serverName
        self._serverAddress = serverAddress
        self._serverPort = serverPort
        self._connect()

    def _connect(self):
        try:
            self._mpdServer = mpd.MPDClient()
            self._mpdServer.connect(self._serverAddress, self._serverPort)
            self._mpdServer.ping()
            return True
        except:
            print "Error connecting MPD"
            return False

    def getPlaylists(self, startsWith = None):
        l = []
        for pl in self._mpdServer.listplaylists():
            if startsWith == None:
                l.append(pl['playlist'])
            elif str(pl['playlist']).startswith(startsWith):
                l.append(pl['playlist'])
        return sorted(l)

    def getServerVersion(self):
        return self._mpdServer.mpd_version

    def getVolume(self):
        return self._mpdServer.status()['volume']

    def volume(self, volume):
        self._mpdServer.setvol(volume)

    def stop(self):
        self._mpdServer.stop()

    def play(self):
        self._mpdServer.play()

    def emptyPlaylist(self):
        self._mpdServer.clear()

    def loadPlaylist(self, name):
        self._mpdServer.load(name)

    def randomize(self, val):
        self._mpdServer.random(val)

class Mpd():

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

        if not self._config.has_section('MPD'):
            print "Adding MPD part"
            update = True
            self._config.add_section("MPD")

        if not self._config.has_option("MPD", "ServerNames"):
            print "No Server Names"
            update = True
            self._config.set("MPD", "ServerNames", "NAME1,NAME2")

        if not self._config.has_option("MPD", "ServerAddresses"):
            print "No Server Addresses"
            update = True
            self._config.set("MPD", "ServerAddresses", "server1,server2")

        if not self._config.has_option("MPD", "ServerPorts"):
            print "No Server Ports"
            update = True
            self._config.set("MPD", "ServerPorts", "6600,6600")

        namesString     = self._config.get("MPD", "ServerNames")
        addressesString = self._config.get("MPD", "ServerAddresses")
        portsString     = self._config.get("MPD", "ServerPorts")

        if namesString == None or addressesString == None or portsString == None:
            print "Error in MPD config Settings"
        else:
            names     = namesString.split(",")
            addresses = addressesString.split(",")
            ports     = portsString.split(",")
            if len(names) != len(addresses) or len(addresses) != len(ports):
                print "Number of MPD configs do not match"
            else:
                for i in range(len(names)):
                    m = MpdServer(names[i].strip(), addresses[i].strip(), ports[i].strip())
                    self._mpdServers[names[i].strip()] = m

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def __init__(self):
        self._mpdServers     = {}
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

    def getServerNames(self):
        return self._mpdServers.keys()

    def getServerbyName(self, name):
        if self._mpdServers.has_key(name):
            return self._mpdServers[name]
        else:
            return None

if __name__ == "__main__":
    print "MPD"

    single = MpdServer("Bath", "bathserver")
    single2 = MpdServer("Bath", "bathserver", 6600)

    m = Mpd()
    print m.getServerNames()

    s = m.getServerbyName('AnsiRoom')
    print s.getPlaylists()
    print s.getPlaylists('Drei ???|Die drei ??? \xe2\x80\x93')
    print s.getServerVersion()
    print s.getVolume()
    s.volume(20)
    s.emptyPlaylist()
    random.seed
    s.loadPlaylist(random.choice(s.getPlaylists('Drei ???|Die drei ??? \xe2\x80\x93')))
    s.play()
