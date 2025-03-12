from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
import json
from datetime import datetime, timezone
import re
from rules import RULES
from db.queriesXTDB import Query

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

        except Exception as error:
            print(f"Error occurred: {error}")

    async def update_user(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds

        params = (timestamp, profile.userId)

        # query = Query.SELECT_USER_BT_VT_AND_NOW

        # async with self.conn.cursor() as cur:
        #     await cur.execute(query, params)
        #     rows = await cur.fetchall()
        #     print(rows)

        query = Query.PATCH_WITH_TIME(profile.attributes)

        async with self.conn.cursor() as cur:
            
            await cur.execute(query, params)

        return profile
        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        query = Query.SELECT_USER
        #query = """SELECT c.*, _valid_from, _valid_to FROM customer AS c WHERE _id = %s"""

        params = (userId,)

        if timestamp is not None: 
            
            query = Query.SELECT_USER_WITH_VT
            
            timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc) #assuming it is in seconds
            params = (timestamp, userId)

        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                return UserProfile(userId=row[0], attributes=row[1], timestamp=int(row[2].timestamp()))
            return None
        
    async def get_all_documents(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        query = Query.SELECT_ALL_CURRENT
        
        query = Query.SELECT_ALL_WITH_TIMES

        #WHY IS THIS NOT WORKING????
        #query = SELECT_NESTED_ARGUMENTS

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
            