import os
import time
import random
import ConfigParser
from watson_developer_cloud import TextToSpeechV1
from Room import Room

class Tts():

    def __init__(self):
        self._homeDir        = os.path.expanduser("~/.sensomatic")
        self._configFileName = self._homeDir + '/config.ini'
        self._config         = ConfigParser.ConfigParser()
        self._readConfig()
        self._ttsDir         = self._config.get("TTS", "TTSDir")
        self._tts            = TextToSpeechV1(username=self._config.get('TTS', 'AuthName'),
                                              password=self._config.get('TTS', 'AuthSecret'),
                                              x_watson_learning_opt_out=False) # Lets learn from our nonsense

        if not os.path.isdir(self._config.get("TTS","TTSDir")):
            print "Creating TTS Dir"
            os.makedirs(self._config.get("TTS","TTSDir"))

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

        if not self._config.has_option("TTS", "TTSDir"):
            print "No TTS Dir"
            update = True
            self._config.set("TTS", "TTSDir", "<TTSDir>")

        if update:
            with open(self._configFileName, 'w') as f:
                self._config.write(f)

    def createWavFile(self, text, room):

        finalDir = self._ttsDir + "/" + room

        if not os.path.isdir(finalDir):
            print "Creating destination Dir"
            os.makedirs(finalDir)

        try:
            filename = "%s-%i-%d" % (room, int(time.time()), random.randint(0,9999999999))
            with open(finalDir + "/" + filename + ".tmp", 'w') as f:
                f.write(self._tts.synthesize(text, accept='audio/wav', voice=self._config.get('TTS', 'Voice')))
            os.rename(finalDir + "/" + filename + ".tmp", finalDir + "/" + filename + ".wav")
        except:
            print "error in TTS"

if __name__ == '__main__':
    t = Tts()
    t.createWavFile("<voice-transformation type='Custom' glottal_tension='-80%'>This is a test</voice-transformation>", Room.ANSI_ROOM)