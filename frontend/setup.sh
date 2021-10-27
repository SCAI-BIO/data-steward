docker stop steward-1

docker rm steward-1

docker build -t data-steward:latest .

docker run -it -d -p 9009:5000 --name steward-1 data-steward:latest


