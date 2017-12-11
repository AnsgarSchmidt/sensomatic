FROM resin/odroid-xu4-debian:latest

RUN curl \
    https://dl.influxdata.com/influxdb/nightlies/influxdb-nightly_linux_armhf.tar.gz \
    | tar -xz --strip-components=2

VOLUME /var/lib/influxdb
EXPOSE 8086
CMD /usr/bin/influxd
