import time
import RPi.GPIO         as GPIO
import paho.mqtt.client as mqtt

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
    print "Mq Received on channel %s -> %s" % (msg.topic, msg.payload)

if __name__ == "__main__":

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(9, GPIO.IN)

    mqclient            = mqtt.Client("ansibedmotion", clean_session=True)
    mqclient.on_connect = on_connect
    mqclient.on_message = on_message
    mqclient.connect("cortex", 1883, 60)

    lastValue  = False
    lastReport = 0

    while True:

        mqclient.loop(max_packets=1000)

        if (GPIO.input(9)):
            if not lastValue or (lastValue and (time.time() - lastReport) > 30):
                mqclient.publish("ansiroom/motion", 1)
                lastValue  = True
                lastReport = time.time()
        else:
            lastValue  = False
            lastReport = 0

        time.sleep(1)
