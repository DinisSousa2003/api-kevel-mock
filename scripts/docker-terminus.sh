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
if [ -f "../scripts/schema.py" ]; then
  cp ../scripts/schema.py schema.py
  echo "Schema copied successfully."
else
  echo "Warning: schema.py not found!"
fi

cp ../scripts/schema.py schema.py #Uncomment when schema is done

#rm schema.py #Comment when schema is done. Check if we can startt without schema

tdbpy commit -m"Schema"

echo "Setup complete!"