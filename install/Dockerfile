# DAC Speech Transcription Platform
FROM ubuntu:14.04

MAINTAINER Daniel van Niekerk <dvn.demitasse@gmail.com>
LABEL Description="Basic speech server served over HTTP using Apache"

#Install standard tools from Ubuntu repo
RUN apt-get update && apt-get install -y apache2 libapache2-mod-proxy-uwsgi uwsgi uwsgi-plugin-python patch python python-bcrypt

#Configure Apache to forward requests (uWSGI)
COPY tech_services/install/* /etc/apache2/sites-available/
RUN patch /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf.patch
RUN a2enmod proxy headers

#Setup user and source code for platform
RUN groupadd -g 1012 dac
RUN useradd -u 1012 -g 1012 -ms /bin/bash dac
ENV HOME=/home/dac
#Next line should correspond to definitions in `speech_server/config/*`
ENV PERSISTENT_FS=/mnt/stp
WORKDIR $HOME

#Install application server
COPY tech_services $HOME/source/speech/
RUN chown -R dac:dac $HOME/source

#Run application server
USER root
WORKDIR $HOME/source/speech/speech_server
CMD chown -R dac:dac $PERSISTENT_FS && \
    /usr/sbin/apache2ctl start && \
    uwsgi --uid 1012 -l 2 -p 1 --master --enable-threads --plugin /usr/lib/uwsgi/plugins/python27_plugin.so --socket 127.0.0.1:9090 --wsgi-file wsgi.py  --env services_config=config/dispatcher.json
