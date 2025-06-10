#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY=~/.ssh/id_ed25519  # Replace with actual path

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'

docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | cut -f1
}

VOLUME="terminusdb-data:/data"
PATH="/data/db"


docker_size=$(docker_du "$VOLUME" "$PATH")


echo "docker_size=$docker_size"

EOF
