# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG REPO_URL=https://github.com/gkochievi/Nokia_XML_Generator.git
ARG BRANCH=main

RUN git clone --depth 1 --branch ${BRANCH} ${REPO_URL} .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p uploads generated example_files

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
