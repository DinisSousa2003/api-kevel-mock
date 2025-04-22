from typing import Optional
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from datetime import datetime, timezone
from db.database import Database
from db.queries.queriesPostgres import QueryState, QueryDiff
from db.queries.helper import merge_with_past, merge_with_future 
from imports.models import UserProfile
from imports.rules import Rules
from imports.test_helper import GetType, PutType
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
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS, row_factory=dict_row)
            print("Connected to Postrges database successfully.")
            
            #CREATE STATE AND DIFF TABLE, IF THEY DON'T EXIST
            #await self.clear_tables()
            await self.create_state_customers_table()
            await self.create_diff_customers_table()
            await self.create_indexes()

        except Exception as error:
            print(f"Error occurred: {error}")

##########################BOTH STATE AND DIFF FUNCTIONS###########################################

    async def clear_tables(self):
        query = QueryState.DROP_TABLE

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            print("Customer state table dropped.")

            query = QueryDiff.DROP_TABLE

            await cur.execute(query)
            print("Customer state table dropped.")

    async def create_indexes(self):
         
        query = QueryState.CREATE_INDEX

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            print("INDEX 1.")

            query = QueryState.CREATE_INDEX2
            await cur.execute(query)
            print("INDEX 2.")

            query = QueryDiff.CREATE_INDEX
            await cur.execute(query)
            print("INDEX 3.")

            query = QueryDiff.CREATE_INDEX2
            await cur.execute(query)
            print("INDEX 4.")




##########################STATE BASED FUNCTIONS#################################################

    async def create_state_customers_table(self):
            query = QueryState.CREATE_TABLE

            async with self.conn.cursor() as cur:
                await cur.execute(query)
                print("Customer state table exists.")

    async def update_user_state(self, profile: UserProfile):

            if self.conn is None:
                raise Exception("Database connection not established")

            dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
            id = profile.userId
            attributes = profile.attributes

            params = (id, dt)

            if not attributes:
                return (None, PutType.NO_UPDATE)
            
            #1. Get most recent valid attributes
            past = {}

            async with self.conn.cursor() as cur:
                query = QueryState.SELECT_USER_AT
                await cur.execute(query, params)
                row = await cur.fetchone()
                if row:
                    past = row['attributes']


            #2. Update attributes for given time
            new_attributes = merge_with_past(past, attributes, self.rules)
            params_w_attr = (id, Jsonb(new_attributes), dt)

            query = QueryState.INSERT_WITH_TIME
            async with self.conn.cursor() as cur:
                await cur.execute(query, params_w_attr)

            
            #3. Get all future states
            async with self.conn.cursor() as cur:
                query = QueryState.SELECT_USER_BT_VT_AND_NOW
                await cur.execute(query, params)
                futures = await cur.fetchall()

            if not futures:
                 return (profile, PutType.MOST_RECENT)

            #4. Update all future states
            for future in futures:
                future = merge_with_future(future, attributes, self.rules)

                params_w_attr = (id, Jsonb(future["attributes"]), future["at"])

                query = QueryState.INSERT_WITH_TIME
                async with self.conn.cursor() as cur:
                    await cur.execute(query, params_w_attr)
            
            return (profile, PutType.PAST)
    

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")
        
        typeResponse = GetType.CURRENT

        if timestamp: 
            query = QueryState.SELECT_USER_AT
            dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc) #ms to seconds
            params = (userId, dt)
            typeResponse = GetType.TIMESTAMP

        else:
            query = QueryState.SELECT_USER
            params = (userId,)
        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                profile = UserProfile(userId=row['id'], attributes=row['attributes'], timestamp=int(row['at'].timestamp()))
                return (profile, typeResponse)
        
        return (None, GetType.NO_USER_AT_TIME)
        
    
    async def get_all_users_state(self):
        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryState.SELECT_ALL_CURRENT

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
        
    async def check_size_state(self):
        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryState.CHECK_SIZE_STATE

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
    

##########################DIFF BASED FUNCTIONS#################################################

    async def create_diff_customers_table(self):
            query = QueryDiff.CREATE_TABLE

            async with self.conn.cursor() as cur:
                await cur.execute(query)
                print("Customer diff table exists.")

    async def update_user_diff(self, profile: UserProfile):

        if self.conn is None:
                raise Exception("Database connection not established")
        
        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        userId = profile.userId
        attributes = profile.attributes

        query = QueryDiff.INSERT_UPDATE

        async with self.conn.cursor() as cur:
                    await cur.execute(query, (userId, Jsonb(attributes), dt))
        
        #WHEN INSERTING DIFFS, THERE IS NO DIFFERENCE IN UPDATE
        return (profile, PutType.MOST_RECENT)
    
    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
                raise Exception("Database connection not established")
        
        typeResponse = GetType.CURRENT
        
        #1. Select all diffs where userId = userId
        if timestamp: 
            query = QueryDiff.SELECT_DIFFS_UP_TO_VT
            
            dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc) #ms to seconds
            params = (userId, dt)
            typeResponse = GetType.TIMESTAMP

        else:
            query = QueryDiff.SELECT_DIFFS
            params = (userId,)

        async with self.conn.cursor() as cur:
            await cur.execute(query, params, prepare=False)
            diffs = await cur.fetchall()

        if not diffs:
            return (None, GetType.NO_USER_AT_TIME)
        
        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:
            attributes = merge_with_past(attributes, diff["attributes"], self.rules)

        #3. <Optional> Merge all updates that are older than x / more than y and cache (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["at"]  # Last applied timestamp
        profile = UserProfile(userId=userId, attributes=attributes, timestamp=int(latest_timestamp.timestamp()))
        return (profile, typeResponse)
    
    async def check_size_diff(self):
        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryDiff.CHECK_SIZE_DIFF

        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            return rows
        
            