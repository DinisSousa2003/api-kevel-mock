#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY=~/.ssh/id_ed25519  # Replace with actual path

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'
docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | awk '{print $1}'
}

VOLUME="xtdb-data-dir:/data"
ROOT="/data"

total_size=$(docker_du "$VOLUME" "$ROOT")
log_size=$(docker_du "$VOLUME" "$ROOT/log")
buffers_size=$(docker_du "$VOLUME" "$ROOT/buffers")

echo "xtdb2_total_size=$total_size"
echo "xtdb2_log_size=$log_size"
echo "xtdb2_buffers_size=$buffers_size"

# Optionally inspect per-table size if applicable (XTDB 2 buffer tables)
TABLES_DIR="$ROOT/buffers/v05/tables"
TABLES=$(docker run --rm -v "$VOLUME" alpine sh -c "ls $TABLES_DIR 2>/dev/null" || true)

for table in $TABLES; do
    echo "xtdb2_table_${table}_size=$(docker_du "$VOLUME" "$TABLES_DIR/$table")"
    echo "xtdb2_table_${table}_data_size=$(docker_du "$VOLUME" "$TABLES_DIR/$table/data")"
    echo "xtdb2_table_${table}_meta_size=$(docker_du "$VOLUME" "$TABLES_DIR/$table/meta")"
done
EOF
