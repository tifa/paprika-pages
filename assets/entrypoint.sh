#!/bin/sh

sass --watch --style=compressed \
    /app/src/scss:/app/src/static/css &

# Limit to a single worker due to a shared in-memory lock handler
huey_consumer.py src.sync.huey --logfile=/var/log/huey.log &

/app/src/app.py > /var/log/app.log 2>&1
