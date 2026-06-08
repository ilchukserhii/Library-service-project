FROM python:3.13-slim
LABEL maintainer="ilchuk.cergey@gmail.com"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/

RUN mkdir -p /app/static

RUN adduser \
    --disabled-password \
    --no-create-home \
    django_user

RUN chown -R django_user /app/static
RUN chmod -R 755 /app/static

EXPOSE 8000

USER django_user