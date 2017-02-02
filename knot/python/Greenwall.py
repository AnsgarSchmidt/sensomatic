from cloudant.client import Cloudant

cloud   = Cloudant("3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix", "24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925", url = "https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com")
cloud.connect()

db   = cloud['usshorizon']
worf = db['_design/ansiroom.json']
data = worf.get_view("bedplant")

for i in data.result:
    try:
        print "%d -> %d" % (int(i['key']), int(i['value']))
    except:
        pass
        #print i
