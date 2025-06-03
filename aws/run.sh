#!/bin/bash

# Usage: ./run.sh <database_name>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <database_name>"
    exit 1
fi

DB_NAME="$1"

#DB_NAME must be one of the following:
VALID_DB_NAMES=("postgres" "xtdb2" "terminus")
if [[ ! " ${VALID_DB_NAMES[@]} " =~ " ${DB_NAME} " ]]; then
    echo "Invalid database name. Valid options are: ${VALID_DB_NAMES[*]}"
    exit 1
fi

# Define your EC2 instance hostnames or IPs
DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
SERVER_MACHINE="ubuntu@ec2-13-219-246-81.compute-1.amazonaws.com"

# Start the database on the DB machine
echo "Starting database '$DB_NAME' on $DATABASE_MACHINE..."
ssh -T -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 $DATABASE_MACHINE << EOF

bash ~/code/"$DB_NAME".sh
EOF

sleep 10

# Copy the correct .env file to the server machine
echo "Copying .env file for '$DB_NAME' to $SERVER_MACHINE..."
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

docker run --env-file .env -p 8000:8000 my-api
EOF
