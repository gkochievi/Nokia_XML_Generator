#!/bin/sh
# Start nginx in background, then gunicorn in foreground
nginx
exec gunicorn -b 127.0.0.1:5000 app:app
