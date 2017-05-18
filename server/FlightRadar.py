import time
import socket
import datetime
from   geopy.distance import vincenty

class FlightRadar():

    #https://github.com/wiseman/node-sbs1
    #http://woodair.net/SBS/Article/Barebones42_Socket_Data.htm

    def __init__(self):
        self._airplanes = {}
        self._loc = (52.5151,13.4394)

    def dump(self):
        print "DUMPING:"
        for a in self._airplanes:
            print self._airplanes[a]

    def decode(self, data):

        l = len(data)

        if l == 10 or l == 11 or l == 22:
            pass
        else:
            return

        id = data[4]
        d  = {}

        if id in self._airplanes:
            d = self._airplanes[id]
        else:
            print "New Aircraft:" + id
            d['FirstSeen'] = time.time()

        d['LastSeen'] = time.time()

        if l == 22:
            if data[1] == "1":
                # print "ES Identification and Category"
                pass
            elif data[1] == "2":
                print "ES Surface Position Message"
                pass
            elif data[1] == "3":
                # print "ES Airborne Position Message"
                pass
            elif data[1] == "4":
                # print "ES Airborne Velocity Message"
                pass
            elif data[1] == "5":
                # print "Surveillance Alt Message"
                pass
            elif data[1] == "6":
                # print "Surveillance ID Message"
                pass
            elif data[1] == "7":
                print "Air To Air Message"
                pass
            elif data[1] == "8":
                # print "All Call Reply"
                pass
            else:
                print "ERROR in MSG:" + data

        if len(data[2]) > 0:
            d["Session ID"]                = data[2]
        if len(data[3]) > 0:
            d["AircraftID"]                = data[3]
        if len(data[4]) > 0:
            d["HexIdent"]                  = data[4]
        if len(data[5]) > 0:
            d["FlightID"]                  = data[5]
        if len(data[6]) > 0:
            d["Date message generated"]    = data[6]
        if len(data[7]) > 0:
            d["Time message generated"]    = data[7]
        if len(data[8]) > 0:
            d["Date message logged"]       = data[8]
        if len(data[9]) > 0:
            d["Time message logged"]       = data[9]

        if l > 10:
            if len(data[10]) > 0:
                d["Callsign"]              = data[10]

        if l == 22:
            if len(data[11]) > 0:
                d["Altitude"]              = data[11]
            if len(data[12]) > 0:
                d["GroundSpeed"]           = data[12]
            if len(data[13]) > 0:
                d["Track"]                 = data[13]
            if len(data[14]) > 0:
                d["Latitude"]              = data[14]
            if len(data[15]) > 0:
                d["Longitude"]             = data[15]
            if len(data[16]) > 0:
                d["VerticalRate"]          = data[16]
            if len(data[17]) > 0:
                d["Squawk"]                = data[17]
            if len(data[18]) > 0:
                d["Alert (Squawk change)"] = data[18]
            if len(data[19]) > 0:
                d["Emergency"]             = data[19]
            if len(data[20]) > 0:
                d["SPI (Ident)"]           = data[20]
            if len(data[21]) > 0:
                d["IsOnGround"]            = data[21]

            if "Emergency"   in d and d["Emergency"]   == 1:
                print "ALARM!!!!"

            if "SPI (Ident)" in d and d["SPI (Ident)"] == 1:
                print "Special Position!!!!"

        self._airplanes[id] = d

    def analyse(self, line):
        elements = line.split(',')

        if len(elements) == 1:
            return

        if len(elements) == 11 or len(elements) == 22 or len(elements) == 10:

            if   elements[0] == "SEL":
                print "SELECTION CHANGE MESSAGE"
                print line
                print len(elements)

            elif elements[0] == "ID":
                #print "NEW ID MESSAGE"
                if len(elements) == 11:
                    self.decode(elements)

            elif elements[0] == "AIR":
                #print "NEW AIRCRAFT MESSAGE"
                if len(elements) == 10:
                    self.decode(elements)

            elif elements[0] == "STA":
                #print "STATUS CHANGE MESSAGE"
                if len(elements) == 11:
                    self.decode(elements)

            elif elements[0] == "CLK":
                print "CLICK MESSAGE"
                print line
                print len(elements)

            elif elements[0] == "MSG":
                #print "TRANSMISSION MESSAGE"
                if len(elements) == 22:
                    self.decode(elements)

            else:
                print "Unknown Message type:" + line

        else:
            #print "Unknown length:" + str(len(elements)) + "==>" + line
            pass

    def checkPosition(self):
        for aid in self._airplanes:
            a = self._airplanes[aid]
            if "Longitude" in a and "Latitude" in a:
                pos = (a["Latitude"], a["Longitude"])
                distance = vincenty(self._loc, pos).m
                if distance < 5000:
                    if "Callsign" in a:
                        print str(datetime.datetime.now()) + " Airplane in range:" + a["Callsign"] + "-> "+ str(distance)

    def cleanList(self):
        clear = []
        for aid in self._airplanes:
            a = self._airplanes[aid]
            t = a['LastSeen']

            if t + 100 < time.time():
                clear.append(aid)

        for i in clear:
            print "Remove:" + i
            del self._airplanes[i]

if __name__ == "__main__":
    s    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fr   = FlightRadar()
    check = time.time()
    clean = time.time()
    s.connect(('ansiserver', 30003))

    while True:
        data  = s.recv(10000)
        lines = data.split('\n')

        for l in lines:
            fr.analyse(l.rstrip())

        if check + 2 < time.time():
            fr.checkPosition()
            check = time.time()

        if clean + 100 < time.time():
            fr.cleanList()
            clean = time.time()

    fr.dump()
    s.close()
