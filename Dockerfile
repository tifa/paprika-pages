FROM python:3.12

ENV PYTHONPATH=/app \
    UV_SYSTEM_PYTHON=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        logrotate nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY ./assets/.bashrc /root/.bashrc
COPY ./assets/entrypoint.sh /opt/entrypoint.sh
COPY ./assets/logrotate /etc/logrotate.d/app

WORKDIR /app

RUN pip install uv

COPY ./assets/entrypoint.sh /opt/entrypoint.sh

RUN npm install -g sass@1.83.4

COPY ./requirements.txt /app/requirements.txt
COPY ./requirements-dev.txt /app/requirements-dev.txt
RUN if [ "${PROJECT_ENVIRONMENT}" = "production" ]; then \
        uv pip install -r /app/requirements.txt; \
    else \
        uv pip install -r /app/requirements-dev.txt; \
    fi

ENTRYPOINT ["sh", "/opt/entrypoint.sh"]
