#!/bin/bash

# Script to set up a new PostgreSQL container

CONTAINER_NAME="postgres"
VOLUME_NAME="pgdata"
IMAGE_NAME="postgres:17.4"

set -o allexport
source ../.env
set +o allexport

docker rm -f "$CONTAINER_NAME"

docker volume rm "$VOLUME_NAME"

docker volume create "$VOLUME_NAME"

echo "Creating new PostgreSQL container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -e POSTGRES_PASSWORD="$KEY" \
  -e POSTGRES_USER="$USERNAME" \
  -e POSTGRES_DB="postgres" \
  -p 5432:5432 \
  -v "$VOLUME_NAME":/var/lib/postgresql/data \
  "$IMAGE_NAME"
