# Run this script while on the db folder
## cd db
## ./../scripts/docker-terminus.sh 

docker rm -f terminusdb

docker volume rm -f terminusdb-data

docker volume create terminusdb-data

docker run -p 6363:6363 \
  --pull always -d -v terminusdb-data:/app/terminusdb/storage \
  --name terminusdb terminusdb/terminusdb-server

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
if [ -f "../scripts/old_schema.py" ]; then
  cp ../scripts/old_schema.py schema.py
  echo "Schema copied successfully."
else
  echo "Warning: schema.py not found!"
fi

tdbpy commit -m"Schema (mock schema just to start project)"

rm schema.py #Remove mock schema 

echo "Setup complete!"