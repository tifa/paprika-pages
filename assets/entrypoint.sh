#!/bin/sh

sass --watch --style=compressed \
    /app/src/scss:/app/src/static/css &

/app/src/app.py
