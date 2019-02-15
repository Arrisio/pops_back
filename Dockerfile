FROM python:3.7-slim
MAINTAINER "suchkov.dv@gmail.com"

RUN apt-get update && apt-get upgrade && apt-get dist-upgrade
RUN apt-get install gcc -y
RUN apt-get install libgeos-dev -y

ADD ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ADD . /app
