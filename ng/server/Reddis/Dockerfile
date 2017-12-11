FROM resin/odroid-xu4-debian:latest

RUN apt update     && \
    apt upgrade -y && \
    apt install -y git build-essential


RUN \
  cd /tmp                                                         && \
  git clone https://github.com/antirez/redis.git                  && \
  cd redis                                                        && \
  make                                                            && \
  make install                                                    && \
  cp -f src/redis-sentinel /usr/local/bin                         && \
  mkdir -p /etc/redis                                             && \
  cp -f *.conf /etc/redis                                         && \
  rm -rf /tmp/redis*                                              && \
  sed -i 's/^\(bind .*\)$/# \1/' /etc/redis/redis.conf            && \
  sed -i 's/^\(daemonize .*\)$/# \1/' /etc/redis/redis.conf       && \
  sed -i 's/^\(dir .*\)$/# \1\ndir \/data/' /etc/redis/redis.conf && \
  sed -i 's/^\(logfile .*\)$/# \1/' /etc/redis/redis.conf

# Define mountable directories.
VOLUME ["/data"]

# Define working directory.
WORKDIR /data

# Define default command.
CMD ["redis-server", "/etc/redis/redis.conf"]

# Expose ports.
EXPOSE 6379

