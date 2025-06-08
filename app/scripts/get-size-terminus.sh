#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY="/path/to/private_key.pem"  # Replace with actual path

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'

# Function for regular docker du
docker_du() {
    local mount=$1
    local path=$2
    local args=$3
    local multiply=${4:-1}
    docker run --rm -v "$mount" alpine du $args "$path" 2>/dev/null | awk -v mul=$multiply '{print $1 * mul}'
}

# Function for pattern-based match inside docker
docker_du_pattern() {
    local mount=$1
    local path=$2
    local pattern=$3
    docker run --rm -v "$mount" alpine sh -c \
        "du -ba $path | grep -E '$pattern' | awk '{sum += \$1} END {print sum}'"
}

VOLUME="terminusdb-data:/data"
PATH="/data/db"

docker_size=$(docker_du "\$VOLUME" "\$PATH" "-s" 1024)
docker_size_apparent=$(docker_du "\$VOLUME" "\$PATH" "-sb")
larch_size=$(docker_du_pattern "\$VOLUME" "\$PATH" "\\.larch$")

echo "docker_size=$total_size"
echo "docker_size_base=$base_size"
echo "docker_size_wal=$wal_size"
EOF
