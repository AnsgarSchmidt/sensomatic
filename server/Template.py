from jinja2 import Template

class TemplateMatcher():

    TIME_HOURLY = "time-hourly.txt"

    def __init__(self):
        pass



if __name__ == '__main__':
    print "Test"
    t = TemplateMatcher()
    print t.HALLO

template = Template("Hello {{ name }}!")
print template.render(name="Hugo humpf")

