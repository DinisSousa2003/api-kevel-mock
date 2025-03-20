from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.rows import dict_row
from datetime import datetime, timezone
from rules import Rules
from db.queriesXTDB import QueryState, QueryDiff
import uuid

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


##########################SAME FOR DIFF AND STATE##############################################
    
    async def erase_all(self):
        query = QueryState.ERASE_ALL
        async with self.conn.cursor() as cur:
            await cur.execute(query)


##########################STATE BASED FUNCTIONS#################################################

    async def update_user_state(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        id = profile.userId
        params = (id, dt)
        params2 = (dt, id)
        
        attributes_to_update = list(profile.attributes.keys())  # Extract attribute names

        if not attributes_to_update:
            return profile
        
        #1. Get most recent valid attributes
        new_attributes = {}

        async with self.conn.cursor() as cur:
            query = QueryState.SELECT_ALL_CURRENT_ATTR_VT
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
                new_attributes[attr] = max(new_attributes.get(attr, float('-inf')), value)

            elif rule == "or":
                new_attributes[attr] = new_attributes.get(attr, False) or value

        
        #3. Get all future states
        async with self.conn.cursor() as cur:
            query = QueryState.SELECT_USER_BT_VT_AND_NOW
            await cur.execute(query, params, prepare=False)
            futures = await cur.fetchall()

        #4. Update is not in the past  
        if not futures:
            query = QueryState.INSERT_WITH_TIME(new_attributes)
            async with self.conn.cursor() as cur:
                await cur.execute(query, params, prepare=False)

        #4. Update is in the past
        else:
            #Update from timestamp to the first _valid_to
            query = QueryState.INSERT_WITH_TIME_PERIOD(new_attributes)
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
                
                #Value is always older than future
                elif rule == "older":
                    future['attributes'][attr] = value
                    
                #Add value to the attributes
                elif rule == "sum":
                    future['attributes'][attr] = (future['attributes'].get(attr, 0)) + value

                #Update if value > current
                elif rule == "max":
                    future['attributes'][attr] = max(future['attributes'].get(attr, float('-inf')), value)

                #Or between current and value
                elif rule == "or":
                    future['attributes'][attr] = value or future['attributes'].get(attr, False)

            #TODO: CAN I DO THIS IS A BATCH (?)
            if future['_valid_to']:
                query = QueryState.INSERT_WITH_TIME_PERIOD(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from'], future['_valid_to']), prepare=False)
            else:
                query = QueryState.INSERT_WITH_TIME(future['attributes'])
                async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, future['_valid_from']), prepare=False)
        
        
        return profile

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryState.SELECT_USER

        params = (userId,)

        if timestamp is not None: 
            
            query = QueryState.SELECT_USER_WITH_VT
            
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) #assuming it is in seconds
            params = (dt, userId)

        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                return UserProfile(userId=row['_id'], attributes=row['attributes'], timestamp=int(row['_valid_from'].timestamp()))
            return None
        
    async def get_all_users_state(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryState.SELECT_ALL_CURRENT

        query = QueryState.SELECT_ALL_VALID_WITH_TIMES
        
        #query = QueryState.SELECT_ALL_WITH_TIMES

        #query = QueryState.SELECT_NESTED_ARGUMENTS

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
        

##########################DIFF BASED FUNCTIONS#################################################
            

    async def update_user_diff(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        userId = profile.userId
        id = uuid.uuid4()

        query = QueryDiff.INSERT_UPDATE(profile.attributes)

        async with self.conn.cursor() as cur:
                    await cur.execute(query, (id, userId, timestamp), prepare=False)
        
        return profile

    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")

        #1. Select all users where userId = userId

        query = QueryDiff.SELECT_DIFF
        params = (userId,)

        if timestamp is not None: 
            
            query = QueryDiff.SELECT_DIFF_UP_TO_VT
            
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) #assuming it is in seconds
            params = (dt, userId)

        async with self.conn.cursor() as cur:
            await cur.execute(query, params, prepare=False)
            diffs = await cur.fetchall()

        
        #print(diffs)
        if not diffs:
            return None
        
        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:
            for attr, value in diff["attributes"].items():
                rule = self.rules.get_rule_by_atrr(attr)

                if rule == "most-recent":
                    attributes[attr] = value  # Take the latest value encountered

                elif rule == "older":
                    attributes[attr] = attributes.get(attr, value)  # Keep the first value encountered

                elif rule == "sum":
                    attributes[attr] = attributes.get(attr, 0) + value  # Accumulate sum

                elif rule == "max":
                    attributes[attr] = max(attributes.get(attr, float('-inf')), value)  # Keep max value

                elif rule == "or":
                    attributes[attr] = attributes.get(attr, False) or value  # Logical OR

        #3. <Optional> Merge all updates that are older than x / more than y (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["_valid_from"]  # Last applied timestamp
        return UserProfile(userId=userId, attributes=attributes, timestamp=int(latest_timestamp.timestamp()))
        
    async def get_all_users_diff(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        #1. SELECT ALL USER IDS

        #2. PERFORM THE GET USER DIFF FOR ALL THE USERS