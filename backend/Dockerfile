# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads generated example_files

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]