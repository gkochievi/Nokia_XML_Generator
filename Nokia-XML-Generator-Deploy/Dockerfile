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
COPY nginx.conf /etc/nginx/sites-enabled/default

EXPOSE 5000 80

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
