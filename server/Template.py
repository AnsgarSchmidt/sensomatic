import time
import datetime
from   jinja2             import Environment
from   jinja2             import PackageLoader
from   Room               import Room
from   InformationFetcher import  InformationFetcher


class TemplateMatcher():

    def __init__(self):
        self._env                = Environment(loader=PackageLoader('Template', 'tts-templates'))
        self._informationFetcher = InformationFetcher()

    def getHourlyTime(self):
        template = self._env.get_template('time-hourly.txt')
        hour = datetime.datetime.now().time().hour
        _,_,temp,_,_,_,_ = self._informationFetcher.getOutdoor()
        return template.render(hour=hour, temp=temp)

    def getAcknowledgeStartWashingMachine(self):
        template = self._env.get_template('acknowledge-start-washing-machine.txt')
        return template.render()

    def getAcknowledgeEndWashingMachine(self):
        template = self._env.get_template('acknowledge-end-washing-machine.txt')
        return template.render()

    def getAcknowledgeEmtyingWashingMachine(self):
        template = self._env.get_template('acknowledge-empty-washing-machine.txt')
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

    def getAcknowledgeEndBath(self, name):
        template = self._env.get_template('acknowledge-end-bath.txt')
        return template.render(name=name)

    def getAcknowledgeDeactivateBath(self, name):
        template = self._env.get_template('acknowledge-deactivate-everything.txt')
        return template.render(name=name)

    def getWateringTheFlower(self, level):
        template = self._env.get_template('watering-the-flower.txt')
        return template.render(level=level)

    def getWashingMachineReady(self, endtime):
        template = self._env.get_template('washingmachine-ready.txt')
        diff = time.time() - endtime
        hours = int(diff / (60.0 * 60.0) )
        minutes = int( (diff - (hours * 60.0 * 60.0)) / 60.0 )
        return template.render(hours=hours, minutes=minutes)

    def getBathShowerUpdate(self):
        name=self._informationFetcher.getWhoIsInBathShower()
        showerbath=self._informationFetcher.getBathOrShower()
        minutes=self._informationFetcher.getTimeInBathShower()
        outtemp,_,_,condition,_,_,_ = self._informationFetcher.getOutdoor()
        temp=self._informationFetcher.getRoomTemp(Room.BATH_ROOM)
        humidity=self._informationFetcher.getRoomHumidity(Room.BATH_ROOM)
        timehour=datetime.datetime.now().time().hour
        timemin=datetime.datetime.now().time().minute
        template = self._env.get_template('bath-shower-update.txt')
        return template.render(name=name, showerbath=showerbath,minutes=minutes,outtemp=outtemp,condition=condition,temp=temp,humidity=humidity,timehour=timehour,timemin=timemin )

    def getTimeToGoToBed(self):
        template = self._env.get_template('time-to-go-to-bed.txt')
        hour = datetime.datetime.now().time().hour + 1
        return template.render(hour=hour)

    def getWakeupText(self, name):
        template   = self._env.get_template('wakeup.txt')
        name       = name
        fraction, degrees, minutes, seconds = self._informationFetcher.getEarthRotationTime()
        messages   = self._informationFetcher.getNumEmailMessages()
        bathtemp   = self._informationFetcher.getRoomTemp(Room.BATH_ROOM)
        bathhum    = self._informationFetcher.getRoomHumidity(Room.BATH_ROOM)
        planettemp, planethum, planetfeels, conditions, winddir, windspeed, gust = self._informationFetcher.getOutdoor()
        prediction = self._informationFetcher.getPrediction()
        astronauts = self._informationFetcher.getAstronauts()
        return template.render(name=name, degrees=degrees, minutes=minutes, seconds=seconds, messages=messages, bathtemp=bathtemp, bathhum=bathhum, planettemp=planettemp, planethum=planethum, planetfeels=planetfeels, conditions=conditions, winddir=winddir, windspeed=windspeed, gust=gust, prediction=prediction, astronauts=astronauts )

    def getBathToMoisty(self):
        template = self._env.get_template('bath-still-to-moisty.txt')
        return template.render()

    def getWorfsTemperature(self, current, delta):
        template = self._env.get_template('worf-temperature.txt')
        return template.render(current=current, delta=delta)

    def getCo2ToHigh(self, room):
        template = self._env.get_template('co2-to-high.txt')
        return template.render(co2=self._informationFetcher.getRoomCo2Level(room))

    def getRadiationToHigh(self, value):
        template = self._env.get_template('radiation-to-high.txt')
        return template.render(value=value)

    def getRadiationHigherThenAverage(self, valuehere, valueavr):
        template = self._env.get_template('radiation-higher-then-average.txt')
        return template.render(valuehere=valuehere, valueavr=valueavr)

    def getParticulateMatterHigherThenAverage(self, p1, p2):
        template = self._env.get_template('particulate-matter-to-high.txt')
        return template.render(p1=p1, p2=p2)

    def getWaterlevelLow(self):
        template = self._env.get_template('tank-waterlevel-low.txt')
        return template.render()

    def getWaterlevelNormal(self):
        template = self._env.get_template('tank-waterlevel-normal.txt')
        return template.render()

if __name__ == '__main__':
    print "Test templates"
    t = TemplateMatcher()
    #print t.getHourlyTime()
    #print t.getAcknowledgeStartWashingMachine()
    #print t.getWashingMachineReady(234234)
    #print t.getTimeToGoToBed()
    print t.getWakeupText('Ansi')
    #print t.getAcknowledgeStartShower('Ansi')
    #print t.getAcknowledgeEndShower('Ansi')
    #print t.getBathShowerUpdate()
    #print t.getWorfsTemperature(12.12, 01.21)
    #print t.getWorfsTemperature(12.12, -1.21)
    #print t.getWorfsTemperature(12.12, 0.0)
    #print t.getCo2ToHigh(Room.ANSI_ROOM)
    #print t.getRadiationToHigh(0.232)
    #print t.getRadiationHigherThenAverage(0.1, 0.09)
    #print t.getWaterlevelLow()
    #print t.getWaterlevelNormal()
    print t.getParticulateMatterHigherThenAverage(2.2, 3.3)