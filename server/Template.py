import datetime
from jinja2 import Template
from jinja2 import Environment
from jinja2 import PackageLoader

class TemplateMatcher():

    def __init__(self):
        self._env = Environment(loader=PackageLoader('Template', 'tts-templates'))

    def getHourlyTime(self):
        template = self._env.get_template('time-hourly.txt')
        hour = datetime.datetime.now().time().hour
        return template.render(hour=hour)

    def getAcknowledgeStartWashingMachine(self):
        template = self._env.get_template('acknowledge-start-washing-machine.txt')
        return template.render()

    def getWashingMachineReady(self):
        template = self._env.get_template('washingmachine-ready.txt')
        return template.render()




if __name__ == '__main__':
    print "Test"
    t = TemplateMatcher()
    print t.getHourlyTime()
    print t.getAcknowledgeStartWashingMachine()
    print t.getWashingMachineReady()




