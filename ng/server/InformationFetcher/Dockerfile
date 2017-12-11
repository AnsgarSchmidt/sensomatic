FROM resin/odroid-xu4-python:3

ADD requirements.txt requirements.txt
RUN pip install -r   requirements.txt
ADD InformationFetcher.py InformationFetcher.py

CMD python InformationFetcher.py