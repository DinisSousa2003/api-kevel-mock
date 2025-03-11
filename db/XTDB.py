from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
import json
from datetime import datetime, timezone
import re

class XTDB(Database):

    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None  # Will hold the connection

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
            "user": parsed_url.username,
        }

        try:
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS, autocommit=True)
            print("Connected to XTDB database successfully.")
            self.conn.adapters.register_dumper(str, pg.types.string.StrDumperVarchar)
            #TODO: POPULATE HERE

        except Exception as error:
            print(f"Error occurred: {error}")


    async def update_user(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds

        # Ensure that we are passing the record directly (not as JSON string)
        params = (timestamp, profile.userId)

        query = f"""PATCH INTO customer FOR VALID_TIME FROM %s RECORDS {{_id: %s, attributes: {json.dumps(profile.attributes)}}};"""
        
        async with self.conn.cursor() as cur:
            
            await cur.execute(query, params)

        return profile
        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        query = """SELECT c.*, _valid_from, _valid_to FROM customer AS c
                WHERE _id = %s"""

        params = (userId,)

        if timestamp: 
            query = """SELECT c.*, _valid_from, _valid_to, _system_from, _system_to FROM customer
                FOR VALID_TIME AS OF TIMESTAMP %s AS c
                WHERE _id = %s"""
            params = (userId, timestamp)

        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                return UserProfile(userId=row[0], attributes=json.loads(row[1]), timestamp=int(row[2].timestamp()))
            return None
        
    async def get_all_documents(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        #query = """SELECT c.*, _valid_from, _valid_to, _system_from, _system_to FROM customer FOR ALL SYSTEM_TIME FOR ALL VALID_TIME AS c"""
        
        #query = """SELECT c.* FROM customer AS c"""

        query = """SELECT c._id, c.attributes, c.attributes['f86a8b7ef428c89ed1f4d36cdf38b5e4'] FROM customer AS c"""

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
            