FROM debian:latest
ARG environment=prod
MAINTAINER Stefan Koch

RUN apt-get clean && apt-get update && apt-get upgrade -y && apt-get install -y \
    awscli \
    gcc \
    g++ \
    git \
    jq \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    python-virtualenv \
    python3-dev
RUN mkdir /opt/skyscraper
RUN mkdir /opt/skyscraper-spiders/example
RUN mkdir /root/.aws

COPY requirements.txt /opt/skyscraper/requirements.txt
COPY docker/entrypoint.sh /opt/skyscraper/entrypoint.sh
COPY docker/dotenv /opt/skyscraper/.env
COPY . /opt/skyscraper/
COPY skyscraper/spiders/example.py /opt/skyscraper-spiders/example/example.py

RUN /bin/bash -c "cd /opt/skyscraper \
    && virtualenv -p /usr/bin/python3 env \
    && source env/bin/activate \
    && pip install --upgrade setuptools \
    && pip install appdirs pyparsing grpcio \
    && pip install --ignore-installed -r requirements.txt \
    && pip install ."

RUN chmod +x /opt/skyscraper/entrypoint.sh

ENTRYPOINT ["/opt/skyscraper/entrypoint.sh"]
CMD ["crawl-next-scheduled"]
