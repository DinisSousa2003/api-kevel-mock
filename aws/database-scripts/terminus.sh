#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run this script while on any folder — it resolves paths safely

docker rm -f terminusdb
docker volume rm -f terminusdb-data

for id in $(docker ps -q)
do
    if [[ $(docker port "${id}") == *"6363"* ]]; then
        echo "stopping container ${id}"
        docker stop "${id}"
    fi
done

docker volume create terminusdb-data

docker run -p 6363:6363 \
  --pull always -d \
  -v terminusdb-data:/app/terminusdb/storage \
  --name terminusdb terminusdb/terminusdb-server:v11
