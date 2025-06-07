#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY="/path/to/private_key.pem"  # Replace with actual path
DOCKER_VOLUME="pgdata:/data"

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'
docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | awk '{print $1}'
}

total_size=$(docker_du "pgdata:/data" "/data")
base_size=$(docker_du "pgdata:/data" "/data/base")
wal_size=$(docker_du "pgdata:/data" "/data/pg_wal")

echo "docker_size=$total_size"
echo "docker_size_base=$base_size"
echo "docker_size_wal=$wal_size"
EOF
