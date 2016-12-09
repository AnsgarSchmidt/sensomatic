import os
import json
import time
import requests
import datetime
import pytz
from flask         import Flask
from flask         import jsonify
from requests.auth import HTTPBasicAuth

SECOND =  1
MINUTE = 60 * SECOND
HOUR   = 60 * MINUTE
DAY    = 24 * HOUR
WEEK   =  7 * DAY

def getCloudantData(start, end):
    auth = HTTPBasicAuth("3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix",
                         "24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925")
    url = "%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
    "https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com", start, end)
    j = json.loads(requests.get(url, auth=auth).content)
    tz = pytz.timezone('Europe/Berlin')

    data = {
        "cols": [
            {"id": "", "label": "Time",        "pattern": "", "type": "string"},
            {"id": "", "label": "Temperature", "pattern": "", "type": "number"},
            {"id": "", "label": "Heater",      "pattern": "", "type": "number"}
        ],
        "rows": []
    }

    for r in j['rows']:
        e = {}
        ti = {}
        ti['v'] = datetime.datetime.fromtimestamp(r['key'], tz=tz)
        te = {}
        te['v'] = r['value']['watertemp']
        he = {}
        he['v'] = (float(r['value']['heater']) * 0.1) + 24.8

        e['c'] = [ti, te, he]
        data['rows'].append(e)

    return data

app = Flask(__name__)

@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

@app.route('/api/data/gaugetemp')
def getGaugeTemp():
    auth = HTTPBasicAuth("3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix", "24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925")
    url = "https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com/usshorizon/_design/livingroom/_view/tank?descending=true&limit=1"
    j = json.loads(requests.get(url, auth=auth).content)
    return jsonify(float(j['rows'][0]['value']['watertemp']))

@app.route('/api/data/gaugeheater')
def getGaugeHeater():
    auth = HTTPBasicAuth("3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix", "24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925")
    url = "https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com/usshorizon/_design/livingroom/_view/tank?descending=true&limit=1"
    j = json.loads(requests.get(url, auth=auth).content)
    return jsonify(float(j['rows'][0]['value']['heater']))

@app.route('/api/data/1week')
def get1Week():
    data = getCloudantData(time.time() - WEEK, time.time())
    return jsonify(data)

@app.route('/api/data/1day')
def get24Day():
    data = getCloudantData(time.time() - DAY, time.time())
    return jsonify(data)

@app.route('/api/data/1hour')
def get1Hour():
    data = getCloudantData(time.time() - HOUR, time.time())
    return jsonify(data)

@app.route('/api/data/1minute')
def get1Minute():
    data = getCloudantData(time.time() - MINUTE, time.time())
    return jsonify(data)

@app.route('/api/data/heaterusage1week')
def getHeaterUsage1Week():
    auth = HTTPBasicAuth("3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix",
                         "24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925")
    url = "%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
    "https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com", time.time() - WEEK, time.time())
    j = json.loads(requests.get(url, auth=auth).content)
    tz = pytz.timezone('Europe/Berlin')

    data = {
        "cols": [
            {"id": "", "label": "Time",        "pattern": "", "type": "string"},
            {"id": "", "label": "Heater", "pattern": "", "type": "number"}
        ],
        "rows": []
    }

    for r in j['rows']:
        e = {}
        ti = {}
        ti['v'] = datetime.datetime.fromtimestamp(r['key'], tz= tz)
        te = {}
        te['v'] = r['value']['watertemp']
        e['c'] = [ti, te]
        data['rows'].append(e)

    return jsonify(data)


if __name__ == "__main__":
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port))
