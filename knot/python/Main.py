import time
from Downlink import Downlink
from Xively import Xively

if __name__ == '__main__':
    print "Start"

    x = Xively()

    while True:
        time.sleep(10000)