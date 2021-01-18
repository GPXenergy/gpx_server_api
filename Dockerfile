FROM python:3.8.0-slim-buster

# Django settings file
ENV DJANGO_SETTINGS_MODULE "gpx_server.settings"

# Django environment settings
ENV GPX_SECRET_KEY ""
ENV GPX_DEBUG ""
ENV GPX_DB_USER ""
ENV GPX_DB_NAME ""
ENV GPX_DB_PASSWORD ""
ENV GPX_DB_HOST ""
ENV GPX_DB_PORT ""

RUN apt update
RUN apt install -yqq build-essential libpq-dev postgresql-client software-properties-common gdal-bin

COPY ./ /gpx
WORKDIR /gpx

RUN pip install -r ./requirements.txt
RUN pip install gunicorn

RUN mkdir /gpx/staticfiles
RUN ./manage.py collectstatic --noinput

EXPOSE 8000
CMD sh ./docker_entry.sh
