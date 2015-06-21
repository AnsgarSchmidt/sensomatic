import time
import schedule

from Persistor import Persistor

def hourAnnounce():
    print "Announce hour"

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
    schedule.every().sunday.at("23:55").do(wakeup)

    while True:
        schedule.run_pending()
        time.sleep(1)