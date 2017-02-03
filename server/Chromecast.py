import pafy
import time
import pychromecast

class Chromecast():

    def __init__(self):
        pass

    def getCastByName(self, castName):
        try:
            casts = pychromecast.get_chromecasts()
            for i in casts:
                if i.device.friendly_name == castName:
                    return i
            return None
        except Exception as e:
            pass

    def playYoutube(self, castName, youtube_id):
        try:
            audiostream = pafy.new("https://www.youtube.com/watch?v="+youtube_id).getbestaudio()
            cast = self.getCastByName(castName)
            cast.wait()
            mc = cast.media_controller
            mc.play_media(audiostream.url, 'audio/'+audiostream.extension)
            mc.block_until_active()
            mc.play()
            cast.disconnect()
        except Exception as e:
            pass

    def playMusicURL(self, castName, url):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            mc = cast.media_controller
            mc.play_media(url, 'audio/mpeg')
            mc.block_until_active()
            mc.play()
            cast.disconnect()
        except Exception as e:
            pass

    def stop(self, castName):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            cast.quit_app()
            cast.disconnect()
        except Exception as e:
            pass

    def volume(self, castName, volume):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            cast.set_volume(volume)
            cast.disconnect()
        except Exception as e:
            pass

    def getVolume(self, castName):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            level = cast.status.volume_level
            cast.disconnect()
            return level
        except Exception as e:
            return 0

    def getDisplayName(self, castName):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            name =  cast.status.display_name
            cast.disconnect()
            return name
        except Exception as e:
            return ""

    def test(self, castName):
        try:
            cast = self.getCastByName(castName)
            cast.wait()
            print(cast.device)
            print(cast.status)
            mc = cast.media_controller
            print(mc.status)
            print (pychromecast.get_possible_app_ids())
            cast.disconnect()
        except Exception as e:
            pass

if __name__ == '__main__':
    print "Test"
    c = Chromecast()
    c.playMusicURL('Chromeansi', 'http://inforadio.de/livemp3')
    time.sleep(1)
    c.volume('Chromeansi', 0.6)
    time.sleep(1)
    c.volume('Chromeansi', 0.1)
    time.sleep(1)
    c.stop('Chromeansi')
    print c.getVolume('Chromeansi')
    print c.getDisplayName('Chromeansi')
    c.stop('Chromeansi')
    #c.test('Chromeansi')
    c.playYoutube('Chromeansi', '0fYL_qiDYf0')
    c.volume('Chromeansi', 0.6)
