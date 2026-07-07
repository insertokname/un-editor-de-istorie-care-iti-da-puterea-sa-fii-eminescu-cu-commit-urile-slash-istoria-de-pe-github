FROM python:3.12

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates gh \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir requests

WORKDIR /app

ARG PATTERN_FILE
COPY ${PATTERN_FILE} /app/pattern.uedicidpsfeccusidpg

COPY watcher/watcher.py /app/watcher.py
COPY un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github.py /app/

RUN mkdir -p /data

ENTRYPOINT ["python3", "/app/watcher.py"]