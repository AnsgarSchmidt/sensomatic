import os
import time
import requests
import threading

SECOND =   1
MINUTE =  60 * SECOND
HOUR   =  60 * MINUTE
DAY    =  24 * HOUR
WEEK   =   7 * DAY
MONTH  =  31 * DAY
YEAR   = 365 * DAY


class DBThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._CLOUDANT_HOST      = os.environ.get("CLOUDANT_HOST",     "localhost")
        self._CLOUDANT_USERNAME  = os.environ.get("CLOUDANT_USERNAME", "admin"    )
        self._CLOUDANT_PASSWORD  = os.environ.get("CLOUDANT_PASSWORD", "admin"    )
        self._CLOUDANT_DB        = os.environ.get("CLOUDANT_DB",       "defaultdb")
        self._heating_percentage = 30
        self.start()

    def get_heating_percentage(self):
        return self._heating_percentage

    def _work(self, start_timestamp):
        URL   = "https://%s/%s/_find" % (self._CLOUDANT_HOST, self._CLOUDANT_DB)
        AUTH  = (self._CLOUDANT_USERNAME, self._CLOUDANT_PASSWORD)
        QUERY = "{\"selector\":{\"timestamp\":{\"$gt\":%f}},\"fields\":[\"livingroom.tank.heater.value\",\"timestamp\"],\"sort\":[{\"timestamp\":\"asc\"}]}" % start_timestamp
        try:
            result = requests.post(URL, data=QUERY, headers={"Content-Type": "application/json"}, auth=AUTH)
            if result.status_code == 200:
                data     = result.json()["docs"]
                lasttime = data[0]['timestamp']
                ontime   = 0
                offtime  = 0

                for entry in data[1:]:

                    if float(entry['livingroom']['tank']['heater']['value']) > 0:
                        ontime += entry['timestamp'] - lasttime
                    else:
                        offtime += entry['timestamp'] - lasttime

                    lasttime = entry['timestamp']

                self._heating_percentage = (ontime / (ontime + offtime) ) * 100

            else:
                print("DB Access result code not ok")
                print(result.status_code)
                print(result.content)

        except Exception as e:
            print("Error accessing db")
            print(e)

    def run(self):
        while True:
            self._work(time.time() - WEEK)
            time.sleep(30 * MINUTE)


if __name__ == "__main__":
    d = DBThread()
    for i in range(60):
        print(d.get_heating_percentage())
        time.sleep(1)
