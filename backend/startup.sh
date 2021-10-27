echo "Starting all Services in [django,]..."

apt-get update 
 
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

systemctl start redis

echo "172.21.20.50 idsn.dzne.de" >> /etc/hosts

apt-get install -y redis-server

systemctl start redis


python3.8 manage.py migrate
 

python3.8 manage.py runserver 8001
#gunicorn -b 0.0.0.0:8001 viewer.wsgi
