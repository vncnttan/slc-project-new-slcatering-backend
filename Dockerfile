FROM python:3.9-alpine as build-stage

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk update && apk add git

COPY requirements.txt .
COPY .env ./.env

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "RestAPI.wsgi:application"]