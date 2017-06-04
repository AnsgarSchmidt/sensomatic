import os
import sys
import time
import threading
import feedparser
import ConfigParser
from   subprocess import call


class Newscatcher(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._link = ""

    def run(self):
        while True:
            try:
                d = feedparser.parse('http://www.tagesschau.de/export/video-podcast/webxl/tagesschau-in-100-sekunden/')
                link = d['entries'][0]['links'][0]['href']
                if self._link != link:
                    print "converting " + link

                    if os.path.isfile("audiodump.wav"):
                        os.remove("audiodump.wav")

                    if os.path.isfile("/var/www/html/news/tagesschau.tmp"):
                        os.remove("/var/www/html/news/tagesschau.tmp")

                    call(["mplayer", "-novideo", "-nocorrect-pts", "-ao", "pcm:waveheader", link])
                    call(["lame", "-V2", "audiodump.wav", "/var/www/html/news/tagesschau.tmp"])

                    if os.path.isfile("audiodump.wav"):
                        os.remove("audiodump.wav")

                    if os.path.isfile("/var/www/html/news/tagesschau.mp3"):
                        os.remove("/var/www/html/news/tagesschau.mp3")

                    os.rename("/var/www/html/news/tagesschau.tmp", "/var/www/html/news/tagesschau.mp3")
                time.sleep(60 * 5)

            except Exception as e:
                print (e)
                time.sleep(23)

if __name__ == '__main__':
    n = Newscatcher()
    n.start()
    time.sleep(10)
