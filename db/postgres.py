from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.rows import dict_row
from datetime import datetime, timezone
from rules import Rules
from db.queries.helper import merge_with_past, merge_with_future 
import os
from dotenv import load_dotenv

class PostgreSQL(Database):

    def __init__(self, db_url):

        load_dotenv('../.env')

        self.db_url = db_url
        self.conn = None  # Will hold the connection
        self.rules = Rules().get_all_rules()

        self.user = os.getenv("USERNAME", "postgres")
        self.key = os.getenv("KEY", "postgres")

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
            "user": self.user,
            "password": self.key,
        }

        print(f"Connecting to: {DB_PARAMS['host']}:{DB_PARAMS['port']}", f"{DB_PARAMS['dbname']}")

        try:
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS)
            print("Connected to Postrges database successfully.")
            self.conn.adapters.register_dumper(str, pg.types.string.StrDumperVarchar)

        except Exception as error:
            print(f"Error occurred: {error}")

##########################BOTH STATE AND DIFF FUNCTIONS###########################################


##########################STATE BASED FUNCTIONS#################################################

# TODO

#immudb does not seem to support time-travelling by comparing to an attribute, and so is unsuitable for this purpose
    

##########################DIFF BASED FUNCTIONS#################################################
    
# TODO