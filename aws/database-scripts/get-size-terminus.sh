#!/bin/bash

if [ $# -ne 7 ]; then
    echo "Usage: $0 <run_time_mins> <mode> <pct_get> <pct_get_now> <user_number> <rate>"
    exit 1
fi

DB_NAME=terminus
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

docker_du_pattern() {
    local mount=$1
    local path=$2
    local pattern=$3
    docker run --rm -v "$mount" alpine sh -c "find $path -type f -name '$pattern' -exec du -b {} + | awk '{sum += \$1} END {print sum}'"
}

VOLUME="terminusdb-data:/data"
ROOT="/data"
ITERATIONS=$((RUN_TIME / STEP_TIME))

echo "timestamp,metric,value" > "$csv_file"

for ((i = 0; i < ITERATIONS + 1; i++)); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    total_size=$(docker_du "$VOLUME" "/data")
    base_size=$(docker_du "$VOLUME" "/data/db")
    larch_size=$(docker_du_pattern "$VOLUME" "/data/db" "*.larch")

    echo "$timestamp,total_size,$total_size"   >> "$csv_file"
    echo "$timestamp,base_size,$base_size"     >> "$csv_file"
    echo "$timestamp,larch_size,$larch_size"   >> "$csv_file"

    sleep "$((STEP_TIME * 60))"
done
