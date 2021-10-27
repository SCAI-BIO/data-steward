echo "Building Clinical Backend image...\n"

docker stop clinical-backend-2

docker rm clinical-backend-2

docker build -t idsn-clinical-backend .

echo "Running Clinical Backend image...\n"

docker run -it -d --name clinical-backend-2 -p 8001:8001 -v $(pwd)/viewer/settings.py:/etc/django_clinical/viewer/settings.py idsn-clinical-backend:latest 
