from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
import json
from datetime import datetime, timezone

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
        
        query = """INSERT INTO customer (_id, attributes)
                VALUES (%s, %s)"""
            
        params = (profile.user_id, json.dumps(profile.attributes))
        
        if profile.timestamp:
            # Convert Unix timestamp to a timezone-aware datetime object
            timestamp_dt = datetime.fromtimestamp(profile.timestamp, tz=timezone.utc)

            query = """INSERT INTO customer (_id, attributes, _valid_from)
                VALUES (%s, %s, %s)"""
            
            params = (profile.user_id, json.dumps(profile.attributes), timestamp_dt)

        
        
        async with self.conn.cursor() as cur:
            
            await cur.execute(query, params)

        return profile
        

    async def get_user(self, user_id: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        query = """SELECT c.*, _valid_from, _valid_to FROM customer AS c
                WHERE _id = %s"""

        params = (user_id,)

        if timestamp: 
            query = """SELECT c.*, _valid_from, _valid_to, _system_from, _system_to FROM customer
                FOR VALID_TIME AS OF TIMESTAMP %s AS c
                WHERE _id = %s"""
            params = (user_id, timestamp)

        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                return UserProfile(user_id=row[0], attributes=json.loads(row[1]), timestamp=int(row[2].timestamp()))
            return None
        
    async def get_all_documents(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        query = """SELECT c.*, _valid_from, _valid_to, system_from, _system_to FROM customer
                FOR ALL SYSTEM_TIME FOR ALL VALID_TIME AS c"""

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
            