# syntax=docker/dockerfile:1

# ── Stage 1: Build React frontend ──
FROM node:20-alpine AS frontend-build

RUN apk add --no-cache git

ARG REPO_URL=https://github.com/gkochievi/Nokia_XML_Generator.git
ARG BRANCH=main
ARG CACHE_BUST=1

WORKDIR /src
RUN git clone --depth 1 --branch ${BRANCH} ${REPO_URL} .

WORKDIR /src/Frontend
RUN npm ci && npm run build

# ── Stage 2: Final image (Python + nginx) ──
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG REPO_URL=https://github.com/gkochievi/Nokia_XML_Generator.git
ARG BRANCH=main
ARG CACHE_BUST=1

RUN git clone --depth 1 --branch ${BRANCH} ${REPO_URL} .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p uploads generated example_files

# Copy built frontend
COPY --from=frontend-build /src/Frontend/dist /var/www/frontend
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5000 80

CMD ["sh", "-c", "nginx && exec gunicorn -b 0.0.0.0:5000 app:app"]
