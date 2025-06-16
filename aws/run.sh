#!/bin/bash

DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
SERVER_MACHINE="ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com"
LOCUST_MACHINE="ubuntu@ec2-44-202-179-1.compute-1.amazonaws.com"
SERVER_PRIVATE_IP="10.0.63.154"

if [ $# -ne 8 ]; then
    echo "Usage: $0 <database_name> <run_time_mins> <step_time_mins> <mode> <pct_get> <pct_get_now> <user_number> <rate>"
    exit 1
fi

DB_NAME="$1"
RUN_TIME="$2"
STEP_TIME="$3"
MODE="$4"
PCT_GET="$5"
PCT_NOW="$6"
USERS="$7"
RATE="$8"

#DB_NAME must be one of the following:
VALID_DB_NAMES=("postgres" "xtdb2" "terminus")
if [[ ! " ${VALID_DB_NAMES[@]} " =~ " ${DB_NAME} " ]]; then
    echo "Invalid database name. Valid options are: ${VALID_DB_NAMES[*]}"
    exit 1
fi

# Define your EC2 instance hostnames or IPs

# Start the database on the DB machine
echo "Starting database '$DB_NAME' on $DATABASE_MACHINE..."
ssh -T -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 $DATABASE_MACHINE << EOF

bash ~/code/database-scripts/"$DB_NAME".sh
EOF

sleep 30 #needed becuase xtdb takes a while to start

# Copy the correct .env file to the server machine
echo "Copying .env file for '$DB_NAME' and starting server on $SERVER_MACHINE..."
ssh -T -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 $SERVER_MACHINE << EOF

for id in \$(docker ps -q)
do
    if docker port "\$id" | grep -q '8000'; then
        echo "Stopping container \$id"
        docker stop "\$id"
    fi
done

cp ~/code/envs/"$DB_NAME".env ~/code/.env

cd ~/code

docker run --env-file .env -d -p 8000:8000 my-api
EOF

sleep 10 #wait for the server to start

# Start the get database size script on the database machine (let it run and continue)
echo "Starting database size script on $DATABASE_MACHINE..."
ssh -T -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 $DATABASE_MACHINE << EOF
cd ~/code

mkdir -p output

pkill -f 'get-size'

nohup bash database-scripts/get-size-"$DB_NAME".sh "$RUN_TIME" "$MODE" "$PCT_GET" "$PCT_NOW" "$USERS" "$RATE" "$STEP_TIME"> /dev/null 2>&1 &

EOF

# Start the locust on the locust machine
echo "Starting locust on $LOCUST_MACHINE..."
ssh -T -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 $LOCUST_MACHINE << EOF
cd ~/code

mkdir -p output

docker rm -f locust 2>/dev/null || true

docker run --rm \
    --name locust \
    --mount type=bind,src=/home/ubuntu/code/output,dst=/app/output \
    locust \
    locust \
    -f locusttest-aws.py \
    --run-time "${RUN_TIME}m" \
    --step-time "$STEP_TIME" \
    --headless \
    -u "$USERS" \
    --mode "$MODE" \
    --pct-get "$PCT_GET" \
    --pct-get-now "$PCT_NOW" \
    --db "$DB_NAME" \
    --time "$RUN_TIME" \
    --user-number "$USERS" \
    --rate "$RATE" \
    --host "http://$SERVER_PRIVATE_IP:8000"
EOF


