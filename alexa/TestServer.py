from   flask import Flask
from   flask import request
import paho.mqtt.client as mqtt

app = Flask(__name__)

@app.route('/api/v1.0/command', methods=['POST'])
def PostCommand():
    if "pass" in request.form and "command" in request.form and "value" in request.form and "room" in request.form:
        with open('passwd.txt', 'r') as myfile:
            passwd = myfile.read().replace('\n', '')
            if passwd == request.form['pass']:

                if "wohnzimmer" == request.form['room']:
                    mqclient.publish("livingroom/light/main", "TOGGLE")
                    print "Livingroom light"

                if "esstisch" == request.form['room']:
                    mqclient.publish("hackingroom/light/main", "TOGGLE")
                    print "hackingroom light"

                if "ansiraum" == request.form['room']:
                    mqclient.publish("ansiroom/light/main", "TOGGLE")
                    print "ansiraum light"

                if "tiffyraum" == request.form['room']:
                    mqclient.publish("tiffyroom/light/main", "TOGGLE")
                    print "tiffyraum light"

                if "kueche" == request.form['room']:
                    mqclient.publish("kitchen/light/main", "TOGGLE")
                    print "kueche light"

    return "Process command request"

if __name__ == '__main__':
    mqclient = mqtt.Client("alexa", clean_session=True)
    mqclient.connect("cortex", 1883, 60)
    mqclient.loop_start()

    app.run(debug=True, port=2342)

