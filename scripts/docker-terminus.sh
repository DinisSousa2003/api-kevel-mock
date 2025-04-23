#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run this script while on any folder — it resolves paths safely

docker rm -f terminusdb
docker volume rm -f terminusdb-data
docker volume create terminusdb-data

docker run -p 6363:6363 \
  --pull always -d \
  -v terminusdb-data:/app/terminusdb/storage \
  --name terminusdb terminusdb/terminusdb-server:v11

# Define the project name
PROJECT_NAME="terminus"

# Wait for TerminusDB to be ready
echo "Waiting for TerminusDB to start..."
sleep 10

# Run the startproject command and provide inputs
{ 
  echo "$PROJECT_NAME"  # Project name
  echo ""  # Press Enter for the default endpoint
} | tdbpy startproject

# Ensure schema.py is present before proceeding
if [ -f "$SCRIPT_DIR/old_schema.py" ]; then
  cp "$SCRIPT_DIR/old_schema.py" schema.py
  echo "Schema copied successfully."
else
  echo "Warning: old_schema.py not found!"
fi

tdbpy commit -m"Schema (mock schema just to start project)"

rm schema.py # Remove mock schema 

echo "Setup complete!"
