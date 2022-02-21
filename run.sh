export LC_ALL=C.UTF-8
export LANG=C.UTF-8

service redis-server start

service --status-all 

service mongod start

service mongodb start 

sleep 5

mongo /var/steward/mongo-init.js

sleep 5

cd /var/steward/

echo "" >> .env.development

echo "VUE_APP_CLINICALURL=${BACKEND_URL}/clinical-backend/api-steward" >> .env.development

echo "VUE_APP_CLINICALURL=${BACKEND_URL}/clinical-backend/api-steward" >> .env.production

npm i 

npm run build

node app_no_auth.js &

cd ..
cd ..

python3.8 /var/django_clinical/manage.py migrate 

python3.8 /var/django_clinical/manage.py runserver 0.0.0.0:8001
