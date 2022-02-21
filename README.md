# Data Steward Tool


## Updates December 2021

- Data Variables can now have synonyms 
- Using synonyms increased mapping capability 


## API Documentation 

https://data-steward-api.api-docs.io/1.0.0/

## License 

Copyright 2021 Developers of Data Steward Tool 

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Setup instructions
### Standard setup (recommended)
#### Prerequisities 
You need to habe a MongoDB running on your machine -> [MongoDB installation manual](https://docs.mongodb.com/manual/administration/install-community/). Once you have this running you can run the mongo-init.js to setup a database and a user. 
Next up you need a RedisDB ->[RedisDB installation manual](https://redis.io/topics/quickstart). There is no need for further configuration of the redis database.
Furthermore you need __Python__ and __Node.js__ installed on your machine.
#### Backend
The backend application is a Django application. Hence we highly encourage you to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once you set up this you can install the requirements via ```pip install -r requirements.txt```. Then you start the application with ```python manage.py runserver```. Before that you need to run: ```python manage.py migrate``` to run the database migrations. Anyway, there a several methods to run a django application -> https://docs.djangoproject.com/en/4.0/howto/deployment/

#### Frontend
Depending if you run the backend on a server (e.g. example.com/data-steward-backend) or on your localhost you have to adjust the the .end.production file in the frontend folder. There is a variabel named ```VUE_APP_CLINICALURL```that needs to adjusted according to the deployment location of the backend application. For example if ```VUE_APP_CLINICALURL=https://example.com/clinical/data-steward/backend/api-steward``` then the backend needs to be hosted here ```https://example.com/clinical/data-steward/backend/```. The standard build uses localhost:8000 as backend locations. Means if you change that you have to run ```npm run build```to build the modified version. If you stick to localhost and after running the bild you start the application with ```node app_no_auth.js```.
### Docker
There is a [docker image](https://hub.docker.com/repository/docker/phwegner/data-steward) available.

## Loading files
After setting up the application you need a data model. For an example instance you can use: model.xslx in this repo. For an example cohort to upload to the DST you can use [this](https://github.com/phwegner/AAD_N_DR). 

For further questions please use the issue board.
