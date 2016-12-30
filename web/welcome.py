import os
import json
import time
import pytz
import requests
import datetime
import ConfigParser
import matplotlib.pyplot  as     plt
import matplotlib.patches as     mpatches
import matplotlib.dates   as     mdates
from   flask              import Flask
from   flask              import jsonify
from   requests.auth      import HTTPBasicAuth
from   twitter            import *

SECOND =  1
MINUTE = 60 * SECOND
HOUR   = 60 * MINUTE
DAY    = 24 * HOUR
WEEK   =  7 * DAY

def getCloudantData(start, end):
    vcap_config    = os.environ.get('VCAP_SERVICES')
    decoded_config = json.loads(vcap_config)
    auth = HTTPBasicAuth(decoded_config['cloudantNoSQLDB'][0]['credentials']['username'],
                         decoded_config['cloudantNoSQLDB'][0]['credentials']['password'])
    url = "https://%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
           decoded_config['cloudantNoSQLDB'][0]['credentials']['host'], start, end)
    j   = json.loads(requests.get(url, auth=auth).content)
    tz  = pytz.timezone('Europe/Berlin')

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
    vcap_config    = os.environ.get('VCAP_SERVICES')
    decoded_config = json.loads(vcap_config)
    auth = HTTPBasicAuth(decoded_config['cloudantNoSQLDB'][0]['credentials']['username'],
                         decoded_config['cloudantNoSQLDB'][0]['credentials']['password'])
    url = "https://%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
           decoded_config['cloudantNoSQLDB'][0]['credentials']['host'], start, end)
    j = json.loads(requests.get(url, auth=auth).content)
    return jsonify(float(j['rows'][0]['value']['watertemp']))

@app.route('/api/data/gaugeheater')
def getGaugeHeater():
    vcap_config    = os.environ.get('VCAP_SERVICES')
    decoded_config = json.loads(vcap_config)
    auth = HTTPBasicAuth(decoded_config['cloudantNoSQLDB'][0]['credentials']['username'],
                         decoded_config['cloudantNoSQLDB'][0]['credentials']['password'])
    url = "https://%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
           decoded_config['cloudantNoSQLDB'][0]['credentials']['host'], start, end)
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
    vcap_config    = os.environ.get('VCAP_SERVICES')
    decoded_config = json.loads(vcap_config)
    auth = HTTPBasicAuth(decoded_config['cloudantNoSQLDB'][0]['credentials']['username'],
                         decoded_config['cloudantNoSQLDB'][0]['credentials']['password'])
    url = "https://%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
           decoded_config['cloudantNoSQLDB'][0]['credentials']['host'], time.time() - WEEK, time.time())
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

def getKeys(data):
    keys = []
    for i in data['rows']:
        keys.append(float(i['key']))
    return keys

def getValue(data, name):
    values = []
    for i in data['rows']:
        values.append(float(i['value'][name]))
    return values

def getDateTime(data, tz):
    keys = []
    for i in data['rows']:
        keys.append(datetime.datetime.fromtimestamp(i['key'], tz=tz))
    return keys

def getModified(data, mulval, addval):
    d = []
    for i in data:
        d.append(addval + (float(i) * mulval) )
    return d

def getBoolean(data):
    d = [False] * len(data)
    for i in range(len(data)):
        if float(data[i]) == 1:
            d[i] = True
    return d

@app.route('/api/twitter/getHeaterID')
def getHeaterID():
    days_to_catch          = 14
    smooth                 = 20
    filtersize             = 8000
    vcap_config            = os.environ.get('VCAP_SERVICES')
    decoded_config         = json.loads(vcap_config)
    configparser           = ConfigParser.ConfigParser()
    configparser.read("config.txt")
    tz                     = pytz.timezone('Europe/Berlin')
    myFmt                  = mdates.DateFormatter('%d.%b %H:%M')
    oauth                  = OAuth(configparser.get("TWITTER", "accesstoken"),
                                   configparser.get("TWITTER", "accesstokensecret"),
                                   configparser.get("TWITTER", "consumerkey"),
                                   configparser.get("TWITTER", "consumersecret")
                                  )
    twittermedia           = Twitter(domain='upload.twitter.com', auth=oauth)
    auth                   = HTTPBasicAuth(decoded_config['cloudantNoSQLDB'][0]['credentials']['username'],
                                           decoded_config['cloudantNoSQLDB'][0]['credentials']['password'])
    url                    = "https://%s/usshorizon/_design/livingroom/_view/tank?descending=false&startkey=%f&endkey=%f" % (
                              decoded_config['cloudantNoSQLDB'][0]['credentials']['host'],
                              time.time() - (days_to_catch * DAY),
                              time.time())
    data                   = json.loads(requests.get(url, auth=auth).content)
    watertemp_patch        = mpatches.Patch(color='blue',   label='Water Temperature')
    airtemp_patch          = mpatches.Patch(color='green',  label='Air Temperature')
    heater_patch           = mpatches.Patch(color='red',    label='Heater active')
    waterlevel_patch       = mpatches.Patch(color='black',  label='Waterlevel')
    humidity_patch         = mpatches.Patch(color='blue',   label='Humidity')
    heaterpercentage_patch = mpatches.Patch(color='red',    label='Heater Percentage')
    sun_patch              = mpatches.Patch(color='orange', label='Sun')
    moon_patch             = mpatches.Patch(color='blue',   label='Moon')
    addwater_patch         = mpatches.Patch(color='pink',   label='AddingWater')
    timeval                = getKeys(data)
    timedt                 = getDateTime(data, tz)
    watertemp              = getValue(data, "watertemp")
    settemp                = getValue(data, "settemp")
    airtemp                = getValue(data, "airtemp")
    heater                 = getValue(data, "heater")
    heaterspecial          = getModified(heater, 0.2, 23.7)
    heaterBoolean          = getBoolean(heater)
    humidity               = getValue(data, "humidity")
    moon                   = getValue(data, "moon")
    sun                    = getValue(data, "sun")
    waterlevel             = getValue(data, "waterlevel")
    waterlevelspecial      = getModified(waterlevel, 0.2, 23.4)
    addingwater            = getValue(data, "addingwater")
    addingwaterspecial     = getModified(addingwater, 0.2, 23.1)
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
        smoothhum[i]     = smoothhum[len(timeval) - smooth - 1]

    # Calculate heater percentage
    for i in range(filtersize, len(timeval)):
        timeOn = 0.0
        for m in range(i - filtersize, i):
            if heaterBoolean[m]:
                timeOn += timeval[m] - timeval[m - 1]
        heaterPercentage[i] = (timeOn / (timeval[i] - timeval[i - filtersize])) * 100

    # Temp
    duration = 5000
    fig = plt.figure(figsize=(42, 23), dpi=1024, edgecolor='yellow')
    fig.gca().set_ylim([22, 26])
    ax = fig.add_subplot(111)
    ax.legend(handles=[watertemp_patch, airtemp_patch, heater_patch, waterlevel_patch, addwater_patch])
    ax.xaxis.set_major_formatter(myFmt)
    ax.plot(timedt[-duration:], watertemp[-duration:],          'blue',
            timedt[-duration:], smoothairtemp[-duration:],      'green',
            timedt[-duration:], heaterspecial[-duration:],      'red',
            timedt[-duration:], waterlevelspecial[-duration:],  'black',
            timedt[-duration:], addingwaterspecial[-duration:], 'pink')
    fig.savefig("test1.png")

    # Percentage
    duration = 20000
    fig = plt.figure(figsize=(42, 23), dpi=1024, edgecolor='yellow')
    fig.gca().set_ylim([10, 50])
    ax = fig.add_subplot(111)
    ax.legend(handles=[heaterpercentage_patch, airtemp_patch, humidity_patch])
    ax.xaxis.set_major_formatter(myFmt)
    ax.plot(timedt[-duration:], heaterPercentage[-duration:], 'red',
            timedt[-duration:], smoothairtemp[-duration:],    'green',
            timedt[-duration:], smoothhum[-duration:],        'blue')
    fig.savefig("test2.png")

    # sun moon
    duration = 70000
    fig = plt.figure(figsize=(42, 23), dpi=1024, edgecolor='yellow')
    fig.gca().set_ylim([-2, 102])
    ax = fig.add_subplot(111)
    ax.legend(handles=[sun_patch, moon_patch])
    ax.xaxis.set_major_formatter(myFmt)
    ax.plot(timedt[-duration:], sun[-duration:],  'orange',
            timedt[-duration:], moon[-duration:], 'blue')
    fig.savefig("test3.png")

    retval = []

    with open("test1.png", "rb") as imagefile:
        imagedata = imagefile.read()
    retval.append(twittermedia.media.upload(media=imagedata))

    with open("test2.png", "rb") as imagefile:
        imagedata = imagefile.read()
    retval.append(twittermedia.media.upload(media=imagedata))

    with open("test3.png", "rb") as imagefile:
        imagedata = imagefile.read()
    retval.append(twittermedia.media.upload(media=imagedata))

    if os.path.exists("test1.png"):
        os.remove("test1.png")

    if os.path.exists("test2.png"):
        os.remove("test2.png")

    if os.path.exists("test3.png"):
        os.remove("test3.png")

    return jsonify(retval)

if __name__ == "__main__":
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port))
