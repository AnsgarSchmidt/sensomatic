import socket

class FlightRadar():

    def __init__(self):
        self._airplanes = {}

def decode11(data):
    # print "Session ID            : " + data[2]
    # print "AircraftID            : " + data[3]
    # print "HexIdent              : " + data[4]
    # print "FlightID              : " + data[5]
    # print "Date message generated: " + data[6]
    # print "Time message generated: " + data[7]
    # print "Date message logged   : " + data[8]
    # print "Time message logged   : " + data[9]
    # print "Callsign              : " + data[10]
    pass

def decode22(data):
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

    # print "Session ID            : " + data[2]
    # print "AircraftID            : " + data[3]
    # print "HexIdent              : " + data[4]
    # print "FlightID              : " + data[5]
    # print "Date message generated: " + data[6]
    # print "Time message generated: " + data[7]
    # print "Date message logged   : " + data[8]
    # print "Time message logged   : " + data[9]
    # print "Callsign              : " + data[10]
    # print "Altitude              : " + data[11]
    # print "GroundSpeed           : " + data[12]
    # print "Track                 : " + data[13]
    # print "Latitude              : " + data[14]
    # print "Longitude             : " + data[15]
    # print "VerticalRate          : " + data[16]
    # print "Squawk                : " + data[17]
    # print "Alert (Squawk change) : " + data[18]
    # print "Emergency             : " + data[19]
    # print "SPI (Ident)           : " + data[20]
    # print "IsOnGround            : " + data[21]

def analyse(line):
    elements = line.split(',')
    if len(elements) > 10:
        if   elements[0] == "SEL":
            print "SELECTION CHANGE MESSAGE"
            print line
            print len(elements)
            pass

        elif elements[0] == "ID":
            #print "NEW ID MESSAGE"
            if len(elements) == 11:
                decode11(elements)

        elif elements[0] == "AIR":
            print "NEW AIRCRAFT MESSAGE"
            print line
            print len(elements)
            pass

        elif elements[0] == "STA":
            #print "STATUS CHANGE MESSAGE"
            if len(elements) == 11:
                decode11(elements)

        elif elements[0] == "CLK":
            print "CLICK MESSAGE"
            print line
            print len(elements)
            pass

        elif elements[0] == "MSG":
            #print "TRANSMISSION MESSAGE"
            if len(elements) == 22:
                decode22(elements)
        else:
            print "Unknown Message type:"+line

TCP_IP      = 'ansiserver'
TCP_PORT    = 30003
BUFFER_SIZE = 10000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
for i in range(1000):
    data = s.recv(BUFFER_SIZE)
    #print str(i) + "->" + str(data)
    lines = data.split('\n')
    for l in lines:
        analyse(l.rstrip())

s.close()
