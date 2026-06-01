#!/bin/sh

python ./manage.py migrate
exec gunicorn gpx_server.wsgi \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 40 \
  --capture-output
