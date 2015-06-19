import os
import requests
import ConfigParser

homeDir        = os.path.expanduser("~/.sensomatic")
configFileName = homeDir + '/config.ini'
config         = ConfigParser.ConfigParser()

def readConfig():
    update = False

    if not os.path.isdir(homeDir):
        print "Creating homeDir"
        os.makedirs(homeDir)

    if os.path.isfile(configFileName):
        print "Config File present"
        config.read(configFileName)
    else:
        print "Config file not found"
        update = True

    if not config.has_section('TTS'):
        print "Adding TTS part"
        update = True
        config.add_section("TTS")

    if not config.has_option("TTS", "ServerURL"):
        print "No Server URL"
        update = True
        config.set("TTS", "ServerURL", "<ServerURL>")

    if not config.has_option("TTS", "AuthName"):
        print "No Server AuthName"
        update = True
        config.set("TTS", "AuthName", "AuthName")

    if not config.has_option("TTS", "AuthSecret"):
        print "No Server AuthSecret"
        update = True
        config.set("TTS", "AuthSecret", "<AuthSecret>")

    if not config.has_option("TTS", "Voice"):
        print "No Server Voice"
        update = True
        config.set("TTS", "Voice", "<Voice>")

    if update:
        with open(configFileName, 'w') as f:
            config.write(f)

def createWavFile(text, filename):

    with open(filename, 'w') as f:
        res = requests.get(config.get('TTS','ServerURL'),
                   auth=(config.get('TTS', 'AuthName'), config.get('TTS', 'AuthSecret')),
                   params={'text': text, 'voice': config.get('TTS', 'Voice'), 'accept': 'audio/wav; codecs=opus'},
                   stream=True,
                   verify=False
                  )
        f.write(res.content)
    return filename

if __name__ == '__main__':

    readConfig()

    createWavFile("This is a test", "/tmp/test.wav")