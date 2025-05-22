#!/bin/bash

# Script to set up a new PostgreSQL container

CONTAINER_NAME="postgres"
VOLUME_NAME="pgdata"
IMAGE_NAME="postgres:17.4"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load environment variables from the parent directory's .env file
set -o allexport
source "$SCRIPT_DIR/../.env"
set +o allexport

docker rm -f "$CONTAINER_NAME"
docker volume rm "$VOLUME_NAME"

for id in $(docker ps -q)
do
    if [[ $(docker port "${id}") == *"5432"* ]]; then
        echo "stopping container ${id}"
        docker stop "${id}"
    fi
done


docker volume create "$VOLUME_NAME"

echo "Creating new PostgreSQL container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -e POSTGRES_PASSWORD="$KEY" \
  -e POSTGRES_USER="$USERNAME" \
  -e POSTGRES_DB="postgres" \
  -e PGDATA="/var/lib/postgresql/data" \
  -p 5432:5432 \
  -v "$VOLUME_NAME":/var/lib/postgresql/data \
  "$IMAGE_NAME"
