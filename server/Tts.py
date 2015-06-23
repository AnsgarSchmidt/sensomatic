import os
import requests
import ConfigParser


class Tts():

    def __init__(self):
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()

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

        if not self._config.has_section('TTS'):
            print "Adding TTS part"
            update = True
            self._config.add_section("TTS")

        if not self._config.has_option("TTS", "ServerURL"):
            print "No Server URL"
            update = True
            self._config.set("TTS", "ServerURL", "https://stream.watsonplatform.net/text-to-speech-beta/api/v1/synthesize")

        if not self._config.has_option("TTS", "AuthName"):
            print "No Server AuthName"
            update = True
            self._config.set("TTS", "AuthName", "AuthName")

        if not self._config.has_option("TTS", "AuthSecret"):
            print "No Server AuthSecret"
            update = True
            self._config.set("TTS", "AuthSecret", "<AuthSecret>")

        if not self._config.has_option("TTS", "Voice"):
            print "No Server Voice"
            update = True
            self._config.set("TTS", "Voice", "VoiceEnUsMichael")

        if update:
            with open(configFileName, 'w') as f:
                self._config.write(f)

    def createWavFile(self, text, filename):

        with open(filename, 'w') as f:
            res = requests.get(self._config.get('TTS','ServerURL'),
                               auth=(self._config.get('TTS', 'AuthName'), self._config.get('TTS', 'AuthSecret')),
                               params={'text': text, 'voice': self._config.get('TTS', 'Voice'), 'accept': 'audio/wav; codecs=opus'},
                               stream=True,
                               verify=False
                              )
            f.write(res.content)

if __name__ == '__main__':

    t = Tts()
    t.createWavFile("This is a test", "/tmp/test.wav")