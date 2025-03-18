from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.rows import dict_row
import json
from datetime import datetime, timezone
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
        params = (id, timestamp)
        params2 = (timestamp, id)
        
        attributes_to_update = list(profile.attributes.keys())  # Extract attribute names

        if not attributes_to_update:
            return profile
        
        #1. Get most recent valid attributes
        new_attributes = {}

        async with self.conn.cursor() as cur:
            query = Query.SELECT_ALL_CURRENT_ATTR_VT
            await cur.execute(query, params2)
            row = await cur.fetchone()
            if row:
                print("Current values:", row)
                new_attributes = row['attributes']


        #2. Update attributes for given time
        for (attr, value) in profile.attributes.items():
            rule = self.rules.get_rule_by_atrr(attr)

            if rule == "most-recent":
                new_attributes[attr] = value
                
            elif rule == "sum":
                new_attributes[attr] = (new_attributes.get(attr) or 0) + value

        
        #3. Get all future states
        async with self.conn.cursor() as cur:
            query = Query.SELECT_USER_BT_VT_AND_NOW
            await cur.execute(query, params)
            futures = await cur.fetchall()
            print("futures for timestamp", timestamp, ": ", futures)

        #4. Update is not in the past  
        if not futures:
            query = Query.INSERT_WITH_TIME(new_attributes)
            async with self.conn.cursor() as cur:
                await cur.execute(query, params)

        #4. Update is in the past
        else:
            #Update from timestamp to the first _valid_to
            query = Query.INSERT_WITH_TIME_PERIOD(new_attributes)
            params3 = params + (futures[0]['_valid_from'], )
            async with self.conn.cursor() as cur:
                await cur.execute(query, params3)

        #5. Update all future states
        for future in futures:
            for (attr, value) in profile.attributes.items():
                rule = self.rules.get_rule_by_atrr(attr)

                if rule == "most-recent":
                    #Value if value does not exist
                    future['attributes'][attr] = (future['attributes'].get(attr) or value)
                    
                if rule == "sum":
                    #Add value to the attributes
                    future['attributes'][attr] = (future['attributes'].get(attr) or 0) + value

            if future['_valid_to']:
                query = Query.INSERT_WITH_TIME_PERIOD(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from'], future['_valid_to']))
            else:
                query = Query.INSERT_WITH_TIME(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from']))
        
        
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

        query = Query.SELECT_ALL_CURRENT

        query = Query.SELECT_ALL_VALID_WITH_TIMES
        
        #query = Query.SELECT_ALL_WITH_TIMES

        #query = Query.SELECT_NESTED_ARGUMENTS

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
            