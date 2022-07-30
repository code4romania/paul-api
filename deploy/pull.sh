cd /root/paul-api || exit

git pull

docker-compose build
docker-compose down
docker-compose up -d
