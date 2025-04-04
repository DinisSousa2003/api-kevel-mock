# Database Instructions

Select the database trough the .env, which will feed the config.py.

## In Memory (NOT UP TO DATE, JUST TO TEST API)
DEBUG = TRUE

## XTDB
DATABASE_URL=postgresql://xtdb-2@localhost:5432/xtdb
DATABASE_NAME=XTDB
DEBUG=false

## TERMINUSDB
DATABASE_URL=http://127.0.0.1:6363/terminus
DATABASE_NAME=TERMINUSDB
DEBUG=false
USERNAME=admin
KEY=root

## IMMUDB
DATABASE_URL=http://127.0.0.1:30842/defaultdb
DATABASE_NAME=IMMUDB
DEBUG=false
USERNAME=immudb
KEY=immudb

## POSTGRES
DATABASE_URL=http://127.0.0.1:5432/postgres
DATABASE_NAME=POSTGRES
DEBUG=false
USERNAME=postgres
KEY=postgres