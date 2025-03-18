# Database Instructions

Select the database trough the .env, which will feed the config.py.

## In Memory
DEBUG = TRUE

## XTDB
DATABASE_URL=postgresql://xtdb-2@localhost:5432/xtdb
DATABASE=XTDB
DEBUG=false

## TERMINUSDB
DATABASE_URL=http://127.0.0.1:6363/terminus
DATABASE=TERMINUSDB
DEBUG=false

