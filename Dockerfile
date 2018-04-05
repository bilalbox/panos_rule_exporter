FROM python:alpine3.6
MAINTAINER Nasir Bilal <bilalbox@gmail.com>

ENV FLASK_APP=/usr/src/app/panos_rule_exporter_ui.py

ADD . / /usr/src/app/

RUN cd /usr/src/app; pip install -r requirements.txt

WORKDIR /usr/src/app

CMD flask run --host=0.0.0.0

EXPOSE 5000

