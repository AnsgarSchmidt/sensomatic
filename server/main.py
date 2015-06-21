import time

from Persistor import Persistor

if __name__ == '__main__':

    print "Starting"

    print "Start Persistor"
    persistor = Persistor()
    persistor.setDaemon(False)
    persistor.start()

