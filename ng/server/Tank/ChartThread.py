import os
import time
import pytz
import datetime
import requests
import threading
import matplotlib.pyplot  as plt
import matplotlib.patches as mpatches
import matplotlib.dates   as mdates

SECOND =   1
MINUTE =  60 * SECOND
HOUR   =  60 * MINUTE
DAY    =  24 * HOUR
WEEK   =   7 * DAY
MONTH  =  31 * DAY
YEAR   = 365 * DAY

WORKING   = 0
REQUESTED = 1
DONE      = 2

class ChartThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._CLOUDANT_HOST      = os.environ.get("CLOUDANT_HOST",     "localhost")
        self._CLOUDANT_USERNAME  = os.environ.get("CLOUDANT_USERNAME", "admin"    )
        self._CLOUDANT_PASSWORD  = os.environ.get("CLOUDANT_PASSWORD", "admin"    )
        self._CLOUDANT_DB        = os.environ.get("CLOUDANT_DB",       "defaultdb")
        self._state              = REQUESTED
        self.start()

    def _draw_chart(self):
        smooth                 = 20
        filtersize             = 8000
        myFmt                  = mdates.DateFormatter('%d.%b %H:%M')
        watertemp_patch        = mpatches.Patch(color='blue',   label='Water')
        airtemp_patch          = mpatches.Patch(color='green',  label='Air')
        heater_patch           = mpatches.Patch(color='red',    label='Heater')
        humidity_patch         = mpatches.Patch(color='blue',   label='Humidity')
        heaterpercentage_patch = mpatches.Patch(color='red',    label='Heater Percentage')
        sun_patch              = mpatches.Patch(color='orange', label='Sun')
        moon_patch             = mpatches.Patch(color='blue',   label='Moon')
        data                   = self._get_cloudant_data()
        timeval                = self._get_keys(data)
        timedt                 = self._get_date_time(data)
        watertemp              = self._get_value(data, "watertemp")
        airtemp                = self._get_value(data, "airtemp"  )
        heater                 = self._get_value(data, "heater"   )
        heaterspecial          = self._get_modified(heater, 0.2, 23)
        heaterBoolean          = self._get_boolean(heater)
        humidity               = self._get_value(data, "humidity")
        moon                   = self._get_value(data, "moon")
        sun                    = self._get_value(data, "sun")
        smoothairtemp          = [0] * len(timeval)
        smoothhum              = [0] * len(timeval)
        heaterPercentage       = [0] * len(timeval)

        # smooth the raw values
        for i in range(smooth, len(timeval) - smooth):
            airdummy = 0.0
            humdummy = 0.0
            for j in range(i - smooth, i + smooth):
                airdummy += airtemp[j]
                humdummy += humidity[j]
            airdummy /= (2.0 * smooth)
            humdummy /= (2.0 * smooth)
            smoothairtemp[i] = airdummy
            smoothhum[i] = humdummy

        for i in range(len(timeval) - smooth, len(timeval)):
            smoothairtemp[i] = smoothairtemp[len(timeval) - smooth - 1]
            smoothhum[i] = smoothhum[len(timeval) - smooth - 1]

        # Calculate heater percentage
        for i in range(filtersize, len(timeval)):
            timeOn = 0.0
            for m in range(i - filtersize, i):
                if heaterBoolean[m]:
                    timeOn += timeval[m] - timeval[m - 1]
            heaterPercentage[i] = (timeOn / (timeval[i] - timeval[i - filtersize])) * 100

        # Temp
        with plt.xkcd():
            duration = 12000
            fig = plt.figure(figsize=(20, 15), dpi=256)
            ax  = fig.add_axes((0.035, 0.068, 0.93, 0.93))
            ax.spines['right'].set_color('none')
            ax.spines['top'].set_color('none')
            ax.plot(timedt[-duration:], watertemp[-duration:],     'blue',
                    timedt[-duration:], smoothairtemp[-duration:], 'green',
                    timedt[-duration:], heaterspecial[-duration:], 'red'
                   )
            ax.legend(handles=[watertemp_patch, airtemp_patch, heater_patch])
            ax.xaxis.set_major_formatter(myFmt)
            fig.autofmt_xdate()
            fig.savefig("temperature.png")

        # Percentage
        with plt.xkcd():
            duration = 20000
            fig = plt.figure(figsize=(20, 15), dpi=256)
            ax  = fig.add_axes((0.035, 0.068, 0.93, 0.93))
            ax.spines['right'].set_color('none')
            ax.spines['top'].set_color('none')
            ax.plot(timedt[-duration:], heaterPercentage[-duration:], 'red',
                    timedt[-duration:], smoothairtemp[-duration:], 'green',
                    timedt[-duration:], smoothhum[-duration:], 'blue')
            ax.legend(handles=[heaterpercentage_patch, airtemp_patch, humidity_patch])
            ax.xaxis.set_major_formatter(myFmt)
            fig.autofmt_xdate()
            fig.savefig("percentage.png")

        # sun moon
        with plt.xkcd():
            duration = 70000
            fig = plt.figure(figsize=(20, 15), dpi=256)
            ax  = fig.add_axes((0.035, 0.068, 0.93, 0.93))
            ax.spines['right'].set_color('none')
            ax.spines['top'].set_color('none')
            ax.plot(timedt[-duration:], sun[-duration:], 'orange',
                    timedt[-duration:], moon[-duration:], 'blue')
            ax.legend(handles=[sun_patch, moon_patch])
            ax.xaxis.set_major_formatter(myFmt)
            fig.autofmt_xdate()
            fig.savefig("sunmoon.png")

    def trigger(self):
        self._state = REQUESTED

    def is_done(self):
        if self._state == DONE:
            return True
        else:
            return False

    def run(self):
        while True:

            if self._state == REQUESTED:
                self._state = WORKING
                self._draw_chart()
                self._state = DONE
                print("DONE")

            time.sleep(1)

    def _get_keys(self, data):
        keys = []
        for i in data:
            keys.append(float(i['key']))
        return keys

    def _get_date_time(self, data):
        keys = []
        for i in data:
            keys.append(datetime.datetime.fromtimestamp(i['key'], tz=pytz.timezone('Europe/Berlin')))
        return keys

    def _get_value(self, data, name):
        values = []
        for i in data:
            if isinstance(i['value'][name], str):
                values.append(float(i['value'][name]))
            elif isinstance(i['value'][name], int) or isinstance(i['value'][name], float):
                values.append(i['value'][name])
            elif i['value'][name] is None:
                values.append(0)
            else:
                print(type(i['value'][name]))
                print(i)
        return values

    def _get_modified(self, data, mulval, addval):
        d = []
        for i in data:
            d.append(addval + (float(i) * mulval))
        return d

    def _get_boolean(self, data):
        d = [False] * len(data)
        for i in range(len(data)):
            if float(data[i]) == 1:
                d[i] = True
        return d

    def _get_cloudant_data(self):
        URL  = "https://%s/%s/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
               self._CLOUDANT_HOST, self._CLOUDANT_DB, time.time() - (10 * DAY), time.time())
        AUTH = (self._CLOUDANT_USERNAME, self._CLOUDANT_PASSWORD)

        try:
            result = requests.get(URL, headers={"Content-Type": "application/json"}, auth=AUTH)

            if result.status_code == 200:
                return result.json()['rows']

            else:
                print("DB Access result code not ok")
                print(result.status_code)
                print(result.content)

        except Exception as e:
            print("Error accessing db")
            print(e)
