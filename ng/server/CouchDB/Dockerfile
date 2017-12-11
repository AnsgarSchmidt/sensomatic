FROM resin/odroid-xu4-debian:stretch

RUN groupadd -r couchdb && useradd -d /usr/src/couchdb -g couchdb couchdb

# download dependencies
RUN apt update -y -qq && apt install -y --no-install-recommends \
    apt-transport-https build-essential ca-certificates \
    curl default-jdk erlang-dev erlang-nox git haproxy \
    libcurl4-openssl-dev libicu-dev libmozjs185-dev \
    libwxgtk3.0 openssl pkg-config python python-sphinx \
    texinfo texlive-base texlive-fonts-extra python-pip \
    texlive-fonts-recommended texlive-latex-extra \
 && pip install sphinx_rtd_theme \
 && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
 && echo 'deb https://deb.nodesource.com/node_9.x stretch main' > /etc/apt/sources.list.d/nodesource.list \
 && echo 'deb-src https://deb.nodesource.com/node_9.x stretch main' >> /etc/apt/sources.list.d/nodesource.list \
 && apt update -y -qq && apt install -y nodejs \
 && npm install -g grunt-cli \
 && cd /usr/src && git clone https://gitbox.apache.org/repos/asf/couchdb.git \
 && cd couchdb && git checkout master \
 && cd /usr/src/couchdb && ./configure && make \
 && apt purge -y binutils build-essential cpp default-jdk git libcurl4-openssl-dev libicu-dev \
    libwxgtk3.0 make nodejs perl pkg-config texinfo texlive-base texlive-fonts-extra \
    texlive-fonts-recommended texlive-latex-extra \
 && apt autoremove -y \
 && apt install -y libicu57 --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* /usr/lib/node_modules src/fauxton/node_modules src/**/.git .git

# permissions
RUN chmod +x /usr/src/couchdb/dev/run && chown -R couchdb:couchdb /usr/src/couchdb

USER couchdb
EXPOSE 5984 15984 25984 35984 15986 25986 35986
WORKDIR /usr/src/couchdb

ENTRYPOINT ["/usr/src/couchdb/dev/run"]
CMD ["--with-haproxy"]
