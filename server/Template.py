import time
import datetime
from jinja2 import Template
from jinja2 import Environment
from jinja2 import PackageLoader
from InformationFetcher import  InformationFetcher

class TemplateMatcher():

    def __init__(self):
        self._env                = Environment(loader=PackageLoader('Template', 'tts-templates'))
        self._informationFetcher = InformationFetcher()

    def getHourlyTime(self):
        template = self._env.get_template('time-hourly.txt')
        hour = datetime.datetime.now().time().hour
        return template.render(hour=hour)

    def getAcknowledgeStartWashingMachine(self):
        template = self._env.get_template('acknowledge-start-washing-machine.txt')
        return template.render()

    def getAcknowledgeEndWashingMachine(self):
        template = self._env.get_template('acknowledge-end-washing-machine.txt')
        return template.render()

    def getAcknowledgeStartShower(self, name):
        template = self._env.get_template('acknowledge-start-shower.txt')
        return template.render(name=name)

    def getAcknowledgeEndShower(self, name):
        template = self._env.get_template('acknowledge-end-shower.txt')
        return template.render(name=name)

    def getAcknowledgeStartBath(self, name):
        template = self._env.get_template('acknowledge-start-bath.txt')
        return template.render(name=name)

    def getAcknowledgeEndShower(self, name):
        template = self._env.get_template('acknowledge-end-shower.txt')
        return template.render(name=name)

    def getWashingMachineReady(self, endtime):
        template = self._env.get_template('washingmachine-ready.txt')
        diff = time.time() - endtime
        hours = int(diff / (60.0 * 60.0) )
        minutes = int( (diff - (hours * 60.0 * 60.0)) / 60.0 )
        return template.render(hours=hours, minutes=minutes)

    def getTimeToGoToBed(self):
        template = self._env.get_template('time-to-go-to-bed.txt')
        hour = datetime.datetime.now().time().hour + 1
        return template.render(hour=hour)

    def getWakeupText(self, name):
        template   = self._env.get_template('wakeup.txt')
        name       = name
        fraction, degrees, minutes, seconds = self._informationFetcher.getEarthRotationTime()
        messages   = self._informationFetcher.getNumEmailMessages()
        bathtemp   = self._informationFetcher.getRoomTemp(InformationFetcher.BATH)
        bathhum    = self._informationFetcher.getRoomHumidity(InformationFetcher.BATH)
        planettemp, planethum, planetfeels, conditions, winddir, windspeed, gust = self._informationFetcher.getOutdoor()
        prediction = self._informationFetcher.getPrediction()
        astronauts = self._informationFetcher.getAstronauts()
        return template.render(name=name, degrees=degrees, minutes=minutes, seconds=seconds, messages=messages, bathtemp=bathtemp, bathhum=bathhum, planettemp=planettemp, planethum=planethum, planetfeels=planetfeels, conditions=conditions, winddir=winddir, windspeed=windspeed, gust=gust, prediction=prediction, astronauts=astronauts )

    def getBathToMoisty(self):
        template = self._env.get_template('bath-still-to-moisty.txt')
        return template.render()

if __name__ == '__main__':
    print "Test"
    t = TemplateMatcher()
    print t.getHourlyTime()
    print t.getAcknowledgeStartWashingMachine()
    print t.getWashingMachineReady(234234)
    print t.getTimeToGoToBed()
    print t.getWakeupText('Ansi')
    print t.getAcknowledgeStartShower('Ansi')
    print t.getAcknowledgeEndShower('Ansi')



