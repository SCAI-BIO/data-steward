FROM ubuntu:18.04

RUN mkdir /var/django_clinical

COPY backend/ /var/django_clinical


RUN apt-get update 

RUN apt-get install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update 

RUN apt-get install -y build-essential


RUN apt-get install -y python3.8

RUN apt-get install -y python3.8-distutils

RUN apt-get install -y python3.8-dev

RUN apt-get install -y curl

RUN apt-get install -y systemd


RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

RUN python3.8 get-pip.py

RUN python3.8 --version 

RUN python3.8 -m pip --version


RUN apt-get install -y redis-server

RUN apt-get install -y build-essential libssl-dev libffi-dev python-dev


RUN python3.8 -m pip install -r /var/django_clinical/requirements.txt

RUN apt-get install -y wget

RUN wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | apt-key add -

RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/5.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list

RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y mongodb

RUN mkdir /var/steward

COPY mongo-init.js /var/steward/mongo-init.js

RUN apt-get install -y npm

RUN apt-get install -y nodejs



COPY frontend/dist/ /var/steward/dist
COPY frontend/package.json /var/steward/package.json
COPY frontend/app_no_auth.js /var/steward/app_no_auth.js


RUN npm install -g express
RUN npm install -g path
RUN npm install -g serve 
RUN npm install -g axios
RUN npm install -g cookie-parser
COPY run.sh run.sh 
EXPOSE 5000
CMD [ "sh", "run.sh"]
 
