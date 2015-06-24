import time
import Queue
import serial
import threading

class SerialDummy():

    def __init__(self):
        print "SerialDummy starts"

    def readline(self):
        return "Hallo"

    def write(self, line):
        print "Should send line %s" % line

class ReceiveThread(threading.Thread):

    def __init__(self, serial):
        threading.Thread.__init__(self)
        self._serial = serial
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            line = self._serial.readline()
            element = line.split(',')
            command = int(element[0])
            if (command == Downlink.COMMAND_ACK):
                print "Ack Comment"
            elif (command == Downlink.COMMAND_ERROR):
                print "Error:%s" % line
            else:
                print "Error unknown command:%s" % line

class SendThread(threading.Thread):

    def __init__(self, serial):
        threading.Thread.__init__(self)
        self._serial = serial
        self._queue  = Queue.Queue()
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            line = self._queue.get()
            print "Send line %s" % line
            self._ser.write(line + "\n")
            self._queue.task_done()
            time.sleep(0.1) # Let the arduino process the command

class Downlink(threading.Thread):

    COMMAND_ACK   = 0
    COMMAND_ERROR = 1

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._serial  = serial.Serial("/dev/tty.usbserial-FTF3M7UA", 115200)
        self._receive = ReceiveThread(serial)
        self._send    = SendThread(serial)

    def run(self):
        print "Starting Main Thread"
        while True:
            pass












if __name__ == '__main__':
    print "Test"

    d = Downlink()
    d.setDaemon(False)
    d.start()

