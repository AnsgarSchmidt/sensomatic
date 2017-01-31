import time
import paho.mqtt.client as mqtt
import os

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
    print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

def getLoadLevel():
    res = os.popen('uptime | cut -c 40- | cut -f 2 -d ":" | cut -d "," -f 1').readline().strip(\
)
    return res

# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

# Return % of CPU used by user as a character string
def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            return(line.split()[1:5])

if __name__ == "__main__":

    systemname = "ansiserver"

    mqclient            = mqtt.Client("sysinfo-"+systemname, clean_session=True)
    mqclient.on_connect = on_connect
    mqclient.on_message = on_message
    mqclient.connect("cortex", 1883, 60)

    while True:
        mqclient.loop(max_packets=1000)
        mqclient.publish(systemname+"/cputemp",      getCPUtemperature())
        mqclient.publish(systemname+"/cpuuserusage", getCPUuse())
        mqclient.publish(systemname+"/loadlevel",    getLoadLevel())
        mqclient.publish(systemname+"/ramfree",      getRAMinfo()[2])
        mqclient.publish(systemname+"/diskused",     getDiskSpace()[3])
        mqclient.loop(max_packets=1000)

        time.sleep(10)
