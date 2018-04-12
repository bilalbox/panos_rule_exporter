FROM python:alpine3.6

RUN adduser -D panos

ADD . / /home/panos/app/

WORKDIR /home/panos/app

ENV FLASK_APP panos_rule_exporter_ui.py

RUN chown -R panos:panos ./; \
    mkdir /home/panos/configs; \
    chmod -R 777 /home/panos/configs ; \
    cd /home/panos/app; \
    python -m venv venv; \
    source venv/bin/activate; \
    pip install -r requirements.txt; \
    venv/bin/pip install gunicorn

USER panos

CMD exec venv/bin/gunicorn -b :5000 --access-logfile - --error-logfile - panos_rule_exporter_ui:app

EXPOSE 5000
