from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.rows import dict_row
import json
from datetime import datetime, timezone
import re
from rules import Rules
from db.queriesXTDB import Query

class XTDB(Database):

    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None  # Will hold the connection
        self.rules = Rules()

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
            "user": parsed_url.username,
        }

        try:
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS, row_factory=dict_row, autocommit=True)
            print("Connected to XTDB database successfully.")
            self.conn.adapters.register_dumper(str, pg.types.string.StrDumperVarchar)

        except Exception as error:
            print(f"Error occurred: {error}")

    async def erase_all(self):
        query = Query.ERASE_ALL
        async with self.conn.cursor() as cur:
            await cur.execute(query)


    async def update_user(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        id = profile.userId
        params = (timestamp, id)
        
        attributes_to_update = list(profile.attributes.keys())  # Extract attribute names

        if not attributes_to_update:
            return profile
        
        current_values = {}
        async with self.conn.cursor() as cur:
            query = Query.SELECT_ALL_CURRENT_ATTR  # Query only relevant attributes
            await cur.execute(query, (id, ))
            row = await cur.fetchone()
            if row:
                current_values = row


        async with self.conn.transaction():
            for (attr, value) in profile.attributes.items():
                rule = self.rules.get_rule_by_atrr(attr)

                #TODO: UPDATE ALL OF THE SAME RULE AT THE SAME TIME

                print(attr, value, rule)

                #TODO: FOR NOW, ASSUME UPDATES COME IN ORDER

                if rule == "most-recent":
                    query = Query.PATCH_MOST_RECENT(attr, value)
                    async with self.conn.cursor() as cur:
                        await cur.execute(query, params)
                    
                elif rule == "sum":
                    print(current_values, attr)
                    current_value = current_values.get(attr, 0)
                    if current_value is None:
                        current_value = 0
                    query = Query.PATCH_SUM(attr, value, current_value)
                    async with self.conn.cursor() as cur:
                        await cur.execute(query, params)

        return profile
        


    async def update_user_all(self, profile: UserProfile):
        """Adds all information, from the current valid time (until indefinetely). Conserves attributes if they don't exist"""

        if self.conn is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds

        params = (timestamp, profile.userId)

        print({json.dumps(profile.attributes)})

        query = Query.PATCH_WITH_TIME(profile.attributes)

        async with self.conn.cursor() as cur:
            
            await cur.execute(query, params)

        return profile
        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        query = Query.SELECT_USER

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

        #query = Query.SELECT_ALL_CURRENT
        
        query = Query.SELECT_ALL_WITH_TIMES

        #query = SELECT_NESTED_ARGUMENTS

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
            