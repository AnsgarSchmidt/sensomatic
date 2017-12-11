FROM resin/odroid-xu4-python:3

ADD requirements.txt requirements.txt
RUN pip install -r   requirements.txt

ADD Tank.py        Tank.py
ADD DBThread.py    DBThread.py
ADD ChartThread.py ChartThread.py

CMD python Tank.py
