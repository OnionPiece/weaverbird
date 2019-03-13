# https://hub.docker.com/_/mysql

docker run --name weaverbird -e MYSQL_ROOT_PASSWORD=admin -d mysql:5.5

# create and drop database exmaples:
# mysql -uroot -padmin -h 172.17.0.2 -e "drop database app"
# mysql -uroot -padmin -h 172.17.0.2 -e "create database app"
