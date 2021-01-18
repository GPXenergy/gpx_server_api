#!/bin/sh

python ./manage.py migrate
gunicorn gpx_server.wsgi -b 127.0.0.1:8000
