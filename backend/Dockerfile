FROM ubuntu:18.04

COPY ./ /etc/django_clinical/


RUN apt-get update 

RUN apt-get install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update 

RUN apt-get install -y build-essential


RUN apt-get install -y python3.8

RUN apt-get install -y python3.8-distutils

RUN apt-get install -y python3.8-dev

RUN apt-get install -y curl

WORKDIR /etc/django_clinical/

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python3.8 get-pip.py

RUN python3.8 --version 

RUN python3.8 -m pip --version


RUN apt-get install -y gunicorn

RUN python3.8 -m pip install -r requirements.txt

RUN echo "172.21.20.50   idsn.dzne.de" >> /etc/hosts



RUN apt-get install -y git


RUN apt install -y npm

RUN apt install -y nodejs


EXPOSE 8001


CMD sh startup.sh  
