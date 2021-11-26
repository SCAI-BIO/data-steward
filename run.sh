export LC_ALL=C.UTF-8
export LANG=C.UTF-8

service redis-server start

service --status-all 

service mongod start

service mongodb start 

mongo /var/steward/mongo-init.js

cd /var/steward/

echo "" >> .env.development

echo "VUE_APP_CLINICALURL=${BACKEND_URL}/clinical-backend/api-steward" >> .env.development

npm i 

npm run serve &

cd ..
cd ..

python3.8 /var/django_clinical/manage.py migrate 

python3.8 /var/django_clinical/manage.py runserver 0.0.0.0:8001
