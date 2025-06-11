#!/bin/bash

# Fetches the entire output folder from the Locust machine using rsync

LOCUST_MACHINE="ubuntu@ec2-44-202-179-1.compute-1.amazonaws.com"
DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
REMOTE_OUTPUT_DIR="/home/ubuntu/code/output/"
LOCAL_OUTPUT_DIR="output-aws"

# Ensure the local output directory exists
mkdir -p "$LOCAL_OUTPUT_DIR"

echo "[INFO] Fetching ALL output from $LOCUST_MACHINE using rsync..."

# Use rsync for efficient transfer
rsync -avz -e "ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes" \
    "$LOCUST_MACHINE:$REMOTE_OUTPUT_DIR" "$LOCAL_OUTPUT_DIR/"

if [ $? -eq 0 ]; then
    echo "[INFO] All output successfully copied to $LOCAL_OUTPUT_DIR/"
else
    echo "[ERROR] Failed to copy output from remote machine."
    exit 1
fi


echo "[INFO] Fetching ALL output from $DATABASE_MACHINE using rsync..."

# Use rsync for efficient transfer
rsync -avz -e "ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes" \
    "$DATABASE_MACHINE:$REMOTE_OUTPUT_DIR" "$LOCAL_OUTPUT_DIR/"

if [ $? -eq 0 ]; then
    echo "[INFO] All output successfully copied to $LOCAL_OUTPUT_DIR/"
else
    echo "[ERROR] Failed to copy output from remote machine."
    exit 1
fi

