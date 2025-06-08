#!/bin/bash

# Configuration
DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
PRIVATE_KEY="/path/to/private_key.pem"  # Replace with actual key path

ssh -o "IdentitiesOnly=yes" -i "$PRIVATE_KEY" "$DATABASE_MACHINE" << 'EOF'
docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | awk '{print $1}'
}

VOLUME="xtdb2-data:/data"
PATH="/data"

# Basic paths
echo "total=\$(docker_du \$VOLUME \$PATH)"
echo "log=\$(docker_du \$VOLUME \$PATH/log)"
echo "buffers=\$(docker_du \$VOLUME \$PATH/buffers)"

# Per-table sizes under buffers/v05/tables
TABLES_DIR="\$PATH/buffers/v05/tables"
TABLES=\$(docker run --rm -v \$VOLUME alpine sh -c "ls \$TABLES_DIR 2>/dev/null" || true)

for table in \$TABLES; do
    echo "tables/\$table=\$(docker_du \$VOLUME \$TABLES_DIR/\$table)"
    echo "tables/data/\$table=\$(docker_du \$VOLUME \$TABLES_DIR/\$table/data)"
    echo "tables/meta/\$table=\$(docker_du \$VOLUME \$TABLES_DIR/\$table/meta)"
done
EOF
