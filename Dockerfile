FROM debian:9.6
MAINTAINER Stefan Koch

# TODO: For each package write a note why it is needed
RUN apt-get clean && apt-get update && apt-get upgrade -y && apt-get install -y \
    # gcc/g++ is required to compile native python modules
    gcc \
    g++ \
    # python3 is required as runtime, python3-dev is required
    # to compile native python modules
    python3-dev \
    # python-virtualenv is required to separate our installation
    # from the standard debian packages
    python-virtualenv \
    # libpq-dev is required for PostgreSQL driver support
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    # tor and privoxy are required for TOR support
    tor \
    privoxy

# Set privoxy config
# Remove listener to IPv6 address, not used by us and not default in
# docker daemon. If required by somebody, change this later.
RUN echo "forward-socks4a / localhost:9050 ." >> /etc/privoxy/config \
    && sed -i '/^listen-address\s\+\[::1\]:8118/d' /etc/privoxy/config

RUN mkdir -p /opt/skyscraper /opt/skyscraper-spiders/example /opt/skyscraper-data
RUN mkdir /root/.aws

COPY requirements.txt /opt/skyscraper/requirements.txt
COPY docker/entrypoint.sh /opt/skyscraper/entrypoint.sh
COPY docker/dotenv /opt/skyscraper/.env
COPY . /opt/skyscraper/
COPY skyscraper/spiders/example.py /opt/skyscraper-spiders/example/example.py

RUN /bin/bash -c "cd /opt/skyscraper \
    && virtualenv -p /usr/bin/python3 env \
    && source env/bin/activate \
    && pip install -r requirements.txt \
    && pip install .[all]"

RUN chmod +x /opt/skyscraper/entrypoint.sh

ENTRYPOINT ["/opt/skyscraper/entrypoint.sh"]
CMD ["crawl-next-scheduled"]
