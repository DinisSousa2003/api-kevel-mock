# Run this script while on the db folder
docker rm -f terminusdb

docker volume rm -f terminusdb-data

docker volume create terminusdb-data

docker run -p 6363:6363 \
  --pull always -d -v terminusdb-data:/app/terminusdb/storage \
  --name terminusdb terminusdb/terminusdb-server

# Define the project name
PROJECT_NAME="terminus"

# Run the startproject command and provide inputs
{ 
  echo "$PROJECT_NAME"  # Project name
  echo ""  # Press Enter for the default endpoint
} | tdbpy startproject

sleep 5

#cp ../scripts/schema.py schema.py #Uncomment when schema is done

rm schema.py #Comment when schema is done. Check if we can startt without schema

tdbpy commit -m"Schema" #Schema does not work, but we need this command to start(?)