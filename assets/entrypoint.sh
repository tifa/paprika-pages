#!/bin/sh

sass --watch --style=compressed \
    /app/src/scss:/app/src/static/css &

huey_consumer.py src.sync.huey --logfile=/var/log/huey.log &

/app/src/app.py > /var/log/app.log 2>&1
