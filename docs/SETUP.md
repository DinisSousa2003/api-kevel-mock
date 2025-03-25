## Requirements

Run the following command:

Python version 3.10.8
```bash
python3 -m pip install -r requirements.txt 
```

## Start the database

Run either of the .sh scripts on the scripts folder

## Start the API

Crate and change a .env file according to the possibilities presented in the env.md file.

The database to be used will be selected accordingly.

```bash
 uvicorn main:app --reload
 ```

## Mock requests

```bash
 curl -X PUT "http://127.0.0.1:8000/users/1234" -H "Content-Type: application/json" -d '{
  "attributes": { "name": "Alice", "email": "alice@example.com" }
}'

 curl -X PUT "http://127.0.0.1:8000/users/4321" -H "Content-Type: application/json" -d '{
  "attributes": { "name": "Dinis", "email": "dinis@example.com" },
  "timestamp": 1710000000
}'
```

```bash
curl -X GET "http://127.0.0.1:8000/users/1234"

curl -X GET "http://127.0.0.1:8000/users/4321?timestamp=1710000000"
```

```json
{
  "attributes": { 
    "name": "Dinis", 
    "email": "dinis@example.com",
    "age": 30,
    "address": { "street": "Rua X", "city": "Porto" }
  },
  "timestamp": 1710000000
}
```

## Get all changes to the database


## If the server does not die

```bash
sudo lsof -i :8000 #To get the PID of the uvicron process
sudo kill -9 <PID>
```
