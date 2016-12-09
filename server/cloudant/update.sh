#!/usr/bin/env bash
export PYTHONIOENCODING=utf8

SERVER="3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com"
USER="3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix"
PASSWD="24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925"
PORT=443
DB=usshorizon
URL=https://${USER}:${PASSWD}@${SERVER}:${PORT}/${DB}/

source /Users/ansi/development/virtualenv/general/bin/activate

couchapp push ansiroom https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix:24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925@3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com:443/usshorizon
couchapp push livingroom https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix:24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925@3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com:443/usshorizon
couchapp push bathroom https://3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix:24b4187fbd39510e84cc2cf10184cebf97ea56b836aab8ce4590ffe6477ae925@3a4d4cf0-aed2-4916-8413-fa0177d2129f-bluemix.cloudant.com:443/usshorizon



#rev=`curl -X GET ${URL}_design/ansiroom 2>/dev/null | python -c "import sys, json; print json.load(sys.stdin)['_rev']"`
#curl -X PUT "${URL}_design/ansiroom?rev=${rev}" --data-binary @ansiroom.txt 2>/dev/null

#rev=`curl -X GET ${URL}_design/livingroom 2>/dev/null | python -c "import sys, json; print json.load(sys.stdin)['_rev']"`
#curl -X PUT "${URL}_design/livingroom?rev=${rev}" --data-binary @livingroom.txt 2>/dev/null

#rev=`curl -X GET ${URL}_design/bathroom 2>/dev/null | python -c "import sys, json; print json.load(sys.stdin)['_rev']"`
#curl -X PUT "${URL}_design/bathroom?rev=${rev}" --data-binary @bathroom.txt 2>/dev/null

#curl -X PUT "${URL}_design/ansiroom"   --data-binary @ansiroom.txt
#curl -X PUT "${URL}_design/livingroom" --data-binary @livingroom.txt
#curl -X PUT "${URL}_design/bathroom"   --data-binary @bathroom.txt
