import time
import schedule
from Tts import Tts
from Template import TemplateMatcher
from Persistor import Persistor

temp = TemplateMatcher()
tts  = Tts()


def

def hourAnnounce():
    print "Announce hour"
    tts.createWavFile(temp.getHourlyTime(), "/tmp/test.wav")

def wakeup():
    print "Wakeup"

if __name__ == '__main__':

    print "Start Persistor"
    persistor = Persistor()
    persistor.setDaemon(True)
    #persistor.start()

    #https://github.com/dbader/schedule

    schedule.every().hour.do(hourAnnounce)
    schedule.every().monday.at("05:30").do(wakeup)
    schedule.every().tuesday.at("05:30").do(wakeup)
    schedule.every().wednesday.at("05:30").do(wakeup)
    schedule.every().thursday.at("05:30").do(wakeup)
    schedule.every().friday.at("05:30").do(wakeup)

    hourAnnounce()

    while True:
        schedule.run_pending()
        time.sleep(1)