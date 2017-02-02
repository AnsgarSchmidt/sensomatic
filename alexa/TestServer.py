import json
from   flask import Flask
from   flask import request
from   flask import Response
import paho.mqtt.client as mqtt

app = Flask(__name__)

@app.route('/', methods=['GET'])
def Homepage():
    return "Hallo Welt"

@app.route('/api/v1.0/discovery', methods=['POST'])
def Discovery():
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        if passwd == request.form['pass']:
            devices = {
            "discoveredAppliances": [
                {
                    "applianceId"         : "ansi-1",
                    "manufacturerName"    : "Ansi",
                    "modelName"           : "Ansi",
                    "version"             : "1",
                    "friendlyName"        : "Ansi",
                    "friendlyDescription" : "Thermostat by Ansi",
                    "isReachable"         : True,
                    "actions"             : [
                                             "setTargetTemperature",
                                             "incrementTargetTemperature",
                                             "decrementTargetTemperature"
                                            ],
                    "additionalApplianceDetails" : {
                        "extraDetail1": "This is a ansi thermostat that is reachable"
                    }
                }
            ]}
            return Response(json.dumps(devices), mimetype='application/json')
        else:
            return "Wrong Passwd"

@app.route('/api/v1.0/action', methods=['POST'])
def Action():
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        if passwd == request.form['pass']:
            print request.form['data']
            return "OK"






if __name__ == '__main__':
    mqclient = mqtt.Client("alexa", clean_session = True)
    mqclient.connect("cortex", 1883, 60)
    mqclient.loop_start()
    app.run(debug = False, port = 9001)

