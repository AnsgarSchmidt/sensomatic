import os
import sys
import pytz
import time
import math
import ephem
import astral
import datetime
import paho.mqtt.client as     mqtt
from   DBThread         import DBThread
from   ChartThread      import ChartThread

SECOND =   1
MINUTE =  60 * SECOND
HOUR   =  60 * MINUTE
DAY    =  24 * HOUR
WEEK   =   7 * DAY
MONTH  =  31 * DAY
YEAR   = 365 * DAY

DAWN   = 0
DAY    = 1
SUNSET = 2
NIGHT  = 3


class Tank:

    def __init__(self):
        self.get_config()
        self._mqclient               = mqtt.Client(clean_session=True)
        self._mqclient.connect(self._MQTT_HOST, self._MQTT_PORT, 60)
        self._mqclient.on_connect    = self._on_connect
        self._mqclient.on_message    = self._on_message
        self._mqclient.on_disconnect = self._on_disconnect
        self._mqclient.loop_start()
        self._db_thread              = DBThread()
        self._chart_thread           = ChartThread()
        self._water_temp             = 23
        self._water_level            = True
        self._air_temp               = 23
        self._heater                 = False
        self._humidity               = 23
        self._day_state              = NIGHT
        self._sun_percentage         = 0
        self._moon_percentage        = 0
        self._timer_graph_update     = 0
        self._timer_fertilizer       = 0
        self._timer_update_tank      = 0
        self._timer_adcust_temp      = 0
        self._waiting_for_new_graph  = False

    def get_config(self):
        self._MQTT_HOST           =       os.environ.get("MQTT_HOST",           "localhost"     )
        self._MQTT_PORT           =   int(os.environ.get("MQTT_PORT",           1883            ))
        self._TEMP_NIGHT          =   int(os.environ.get("TEMP_NIGHT",          23              ))
        self._TEMP_DAY            =   int(os.environ.get("TEMP_DAY",            24              ))
        self._LOCATION            =       os.environ.get("LOCATION",            "Port of Spain" )
        self._OFFSET              =   int(os.environ.get("OFFSET",              0               ))
        self._INTERVAL_FERTILIZER =   int(os.environ.get("INTERVAL_FERTILIZER", 3600            ))
        self._INTERVAL_GRAPH      =   int(os.environ.get("INTERVAL_GRAPH",      9000            ))
        self._LATITUDE            = float(os.environ.get("LATITUDE",            12.12           ))
        self._LOGITUDE            = float(os.environ.get("LOGITUDE",            13.13           ))
        self._ELEVATION           = float(os.environ.get("ELEVATION",           23.42           ))

    def _on_connect(self, client, userdata, rc, msg):
        print("Connected Tank with result code %s" % rc)
        self._mqclient.subscribe("livingroom/tank/#")

    def _on_message(self, client, userdata, msg):

        if msg.topic == "livingroom/tank/watertemp":
            self._water_temp = float(msg.payload)

        if msg.topic == "livingroom/tank/waterlevel":
            if msg.payload == "1.00":
                self._water_level = True
            else:
                self._water_level = False

        if msg.topic == "livingroom/tank/airtemp":
            self._air_temp = float(msg.payload)

        if msg.topic == "livingroom/tank/heater":
            if msg.payload == "1.00":
                self._heater = True
            else:
                self._heater = False

        if msg.topic == "livingroom/tank/humidity":
            self._humidity = float(msg.payload)

    def _on_disconnect(self, client, userdata, msg):
        print("Disconnect MQTTRulez")
        time.sleep(10)
        sys.exit(1)

    def _updateSunAndMoon(self):
        now                = datetime.datetime.now()
        a                  = astral.Astral()
        a.solar_depression = 'civil'
        city               = a[self._LOCATION]
        sun                = city.sun(date=datetime.date.today(), local=False)
        dawn               = sun['dawn'].replace(tzinfo=None)    + datetime.timedelta(hours=self._OFFSET)
        sunrise            = sun['sunrise'].replace(tzinfo=None) + datetime.timedelta(hours=self._OFFSET)
        sunset             = sun['sunset'].replace(tzinfo=None)  + datetime.timedelta(hours=self._OFFSET)
        dusk               = sun['dusk'].replace(tzinfo=None)    + datetime.timedelta(hours=self._OFFSET)
        moon_phase         = city.moon_phase(date=datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')))
        observer           = ephem.Observer()
        observer.lon       = self._LOGITUDE
        observer.lat       = self._LATITUDE
        observer.elevation = self._ELEVATION
        observer.date      = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin'))
        moon               = ephem.Moon(observer)
        moon_elevation     = moon.alt * (180 / math.pi)

        if dawn < now < sunrise:
            duration             = sunrise - dawn
            done                 = now - dawn
            self._day_state      = DAWN
            self._sun_percentage = int((done.total_seconds() / duration.total_seconds()) * 100)

        elif sunrise < now < sunset:
            self._day_state      = DAY
            self._sun_percentage = 100

        elif sunset < now < dusk:
            duration              = dusk - sunset
            done                  = now - sunset
            self._day_state       = SUNSET
            self._sun_percentage  = int((1.0 - (done.total_seconds() / duration.total_seconds())) * 100)

        else:
            self._day_state       = NIGHT
            self._sun_percentage  = 0

        if 0 <= moon_phase <= 14:
            moon_phase_percentage = 1.0 - ( (14.0 - (moon_phase       ) ) / 14.0)
        else:
            moon_phase_percentage =       ( (14.0 - (moon_phase - 14.0) ) / 14.0)

        if moon_elevation > 0:
            self._moon_percentage = int(moon_phase_percentage * (moon_elevation / 90.0) * 100)
        else:
            self._moon_percentage = 0

    def _publish_mqtt(self):
        self._mqclient.publish("livingroom2/tank/whitelight", self._sun_percentage )
        self._mqclient.publish("livingroom2/tank/bluelight",  self._moon_percentage)

        if self._day_state in (DAWN, DAY, SUNSET):
            self._mqclient.publish("livingroom2/tank/settemp", self._TEMP_DAY)
        else:
            self._mqclient.publish("livingroom2/tank/settemp", self._TEMP_NIGHT)

    def process(self):

        while True:

            if time.time() - self._timer_graph_update > self._INTERVAL_GRAPH:
                print("updating graph")
                self._chart_thread.trigger()
                self._waiting_for_new_graph = True
                self._timer_graph_update    = time.time()

            if self._waiting_for_new_graph and self._chart_thread.is_done():
                self._waiting_for_new_graph = False
                print("Publish graph")

            if time.time() - self._timer_fertilizer > self._INTERVAL_FERTILIZER:
                print("fertilizer")
                if self._day_state == DAY:
                    self._mqclient.publish("livingroom/tank/fertilizer", 1)
                self._timer_fertilizer = time.time()

            if time.time() - self._timer_update_tank > 10:
                print("update tank")
                self._updateSunAndMoon()
                self._publish_mqtt()
                self._timer_update_tank = time.time()

            if time.time() - self._timer_adcust_temp > (6 * HOUR):
                if self._db_thread.get_heating_percentage() > 30:
                    self._TEMP_DAY -= 1
                if self._db_thread.get_heating_percentage() < 30:
                    self._TEMP_DAY += 1
                self._timer_adcust_temp = time.time()

            time.sleep(1)


if __name__ == "__main__":
    t = Tank()
    for i in range(10):
        print("----------- TANK ---------------")
        time.sleep(1)
    t.process()

