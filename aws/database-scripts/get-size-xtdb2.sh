#!/bin/bash

if [ $# -ne 7 ]; then
    echo "Usage: $0 <run_time_mins> <mode> <pct_get> <pct_get_now> <user_number> <rate>"
    exit 1
fi

DB_NAME=xtdb2
RUN_TIME="$1"
MODE="$2"
PCT_GET="$3"
PCT_NOW="$4"
USERS="$5"
RATE="$6"
STEP_TIME="$7"


output_folder="output/$DB_NAME/$MODE/time-$RUN_TIME-users-$USERS-gpt-$PCT_GET-now-$PCT_NOW-rate-$RATE"

mkdir -p "$output_folder"
csv_file="$output_folder/size.csv"

docker_du() {
    local mount=$1
    local path=$2
    docker run --rm -v "$mount" alpine du -sb "$path" 2>/dev/null | awk '{print $1}'
}

VOLUME="xtdb-data-dir:/data"
ROOT="/data"
TABLES_DIR="$ROOT/buffers/v05/tables"
ITERATIONS=$((RUN_TIME / STEP_TIME))

echo "timestamp,metric,value" > "$csv_file"

for ((i = 0; i < ITERATIONS + 1; i++)); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    total_size=$(docker_du "$VOLUME" "$ROOT")
    log_size=$(docker_du "$VOLUME" "$ROOT/log")
    buffers_size=$(docker_du "$VOLUME" "$ROOT/buffers")

    echo "$timestamp,total_size,$total_size"       >> "$csv_file"
    echo "$timestamp,log_size,$log_size"           >> "$csv_file"
    echo "$timestamp,buffers_size,$buffers_size"   >> "$csv_file"

    TABLES=$(docker run --rm -v "$VOLUME" alpine sh -c "ls $TABLES_DIR 2>/dev/null" || true)

    for table in $TABLES; do
        table_path="$TABLES_DIR/$table"
        size=$(docker_du "$VOLUME" "$table_path")
        data_size=$(docker_du "$VOLUME" "$table_path/data")
        meta_size=$(docker_du "$VOLUME" "$table_path/meta")

        echo "$timestamp,table_${table}_size,$size"         >> "$csv_file"
        echo "$timestamp,table_${table}_data_size,$data_size" >> "$csv_file"
        echo "$timestamp,table_${table}_meta_size,$meta_size" >> "$csv_file"
    done

    sleep "$((STEP_TIME * 60))"
done
