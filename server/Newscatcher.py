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
            d = feedparser.parse('http://www.tagesschau.de/export/video-podcast/webxl/tagesschau-in-100-sekunden/')
            link = d['entries'][0]['links'][0]['href']
            if self._link != link:
                print "converting " + link
                call(["mplayer", "-novideo", "-nocorrect-pts", "-ao", "pcm:waveheader", link])
                call(["lame", "-V2", "audiodump.wav", "/var/www/html/news/tagesschau.tmp"])
                os.remove("audiodump.wav")
                os.remove("/var/www/html/news/tagesschau.mp3")
                os.rename("/var/www/html/news/tagesschau.tmp", "/var/www/html/news/tagesschau.mp3")
            time.sleep(60 * 5)

if __name__ == '__main__':
    n = Newscatcher()
    n.start()
    time.sleep(10)
