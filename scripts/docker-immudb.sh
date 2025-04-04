docker rm -f immudb

docker volume rm immudb_data immudb_config immudb_logs

docker volume create immudb_data
docker volume create immudb_config
docker volume create immudb_logs

docker run -d -it  \
    --name immudb \
    -p 30842:3322 \
    -p 30077:9497  \
    -p 32641:8080 \
    -v immudb_data:/var/lib/immudb \
    -v immudb_config:/etc/immudb \
    -v immudb_logs:/var/log/immudb \
    codenotary/immudb:1.9.6

#https://computingpost.medium.com/run-immudb-sql-and-key-value-database-on-docker-kubernetes-15f22391dca5