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
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS, row_factory=dict_row, autocommit=True, prepare_threshold=0)
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
            await cur.execute(query, params2, prepare=False)
            row = await cur.fetchone()
            if row:
                new_attributes = row['attributes']


        #2. Update attributes for given time
        for (attr, value) in profile.attributes.items():
            rule = self.rules.get_rule_by_atrr(attr)

            #More recent than past
            if rule == "most-recent":
                new_attributes[attr] = value

            #If exists, is older, else update
            elif rule == "older":
                new_attributes[attr] = new_attributes.get(attr, value)
                
            #Get value and sum
            elif rule == "sum":
                new_attributes[attr] = new_attributes.get(attr, 0) + value

            #Update if value > current
            elif rule == "max":
                new_attributes[attr] = max(new_attributes.get(attr, 0), value)

            elif rule == "or":
                new_attributes[attr] = new_attributes.get(attr, False) or value

        
        #3. Get all future states
        async with self.conn.cursor() as cur:
            query = Query.SELECT_USER_BT_VT_AND_NOW
            await cur.execute(query, params, prepare=False)
            futures = await cur.fetchall()

        #4. Update is not in the past  
        if not futures:
            query = Query.INSERT_WITH_TIME(new_attributes)
            async with self.conn.cursor() as cur:
                await cur.execute(query, params, prepare=False)

        #4. Update is in the past
        else:
            #Update from timestamp to the first _valid_to
            query = Query.INSERT_WITH_TIME_PERIOD(new_attributes)
            params3 = params + (futures[0]['_valid_from'], )
            async with self.conn.cursor() as cur:
                await cur.execute(query, params3, prepare=False)

        #5. Update all future states
        for future in futures:
            for (attr, value) in profile.attributes.items():
                rule = self.rules.get_rule_by_atrr(attr)

                #Value if value does not exist (future is more recent)
                if rule == "most-recent":
                    future['attributes'][attr] = future['attributes'].get(attr, value)
                
                #Value is older than future
                elif rule == "older":
                    future['attributes'][attr] = value
                    
                #Add value to the attributes
                elif rule == "sum":
                    future['attributes'][attr] = (future['attributes'].get(attr, 0)) + value

                #Update if value > current
                elif rule == "max":
                    new_attributes[attr] = max(new_attributes.get(attr, None), value)

                elif rule == "or":
                    new_attributes[attr] = new_attributes[attr] or value

            if future['_valid_to']:
                query = Query.INSERT_WITH_TIME_PERIOD(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from'], future['_valid_to']), prepare=False)
            else:
                query = Query.INSERT_WITH_TIME(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from']), prepare=False)
        
        
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
                return UserProfile(userId=row['_id'], attributes=row['attributes'], timestamp=int(row['_valid_from'].timestamp()))
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
            