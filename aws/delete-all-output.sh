#!/bin/bash

# Deletes the contents of the output folders on both remote machines

LOCUST_MACHINE="ubuntu@ec2-44-202-179-1.compute-1.amazonaws.com"
DATABASE_MACHINE="ubuntu@ec2-44-222-181-38.compute-1.amazonaws.com"
REMOTE_OUTPUT_DIR="/home/ubuntu/code/output/"

SSH_OPTIONS="-i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes"

echo "[INFO] Deleting contents of $REMOTE_OUTPUT_DIR on $LOCUST_MACHINE..."
ssh $SSH_OPTIONS "$LOCUST_MACHINE" "sudo rm -rf ${REMOTE_OUTPUT_DIR}/*"

if [ $? -eq 0 ]; then
    echo "[INFO] Output directory on $LOCUST_MACHINE cleared."
else
    echo "[ERROR] Failed to clear output directory on $LOCUST_MACHINE."
    exit 1
fi

echo "[INFO] Deleting contents of $REMOTE_OUTPUT_DIR on $DATABASE_MACHINE..."
ssh $SSH_OPTIONS "$DATABASE_MACHINE" "sudo rm -rf ${REMOTE_OUTPUT_DIR}/*"

if [ $? -eq 0 ]; then
    echo "[INFO] Output directory on $DATABASE_MACHINE cleared."
else
    echo "[ERROR] Failed to clear output directory on $DATABASE_MACHINE."
    exit 1
fi
