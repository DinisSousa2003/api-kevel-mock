#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY=~/.ssh/id_ed25519  # Replace with actual path

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'
docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | awk '{print $1}'
}

docker_du_pattern() {
    local mount=$1
    local path=$2
    local pattern=$3
    docker run --rm -v "$mount" alpine sh -c du -ba "$path" 2>/dev/null | awk '{{sum += $1}} END {{print sum}}'
}

VOLUME="terminusdb-data:/data"

total_size=$(docker_du "$VOLUME" "/data")
base_size=$(docker_du "$VOLUME" "/data/db")
larch_size=$(docker_du_pattern "$VOLUME" "/data/db" "\\.larch$")

echo "docker_size=$total_size"
echo "docker_size_base=$base_size"
echo "docker_size_larch=$larch_size"
EOF