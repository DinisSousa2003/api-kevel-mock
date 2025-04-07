from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import psycopg as pg
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from datetime import datetime, timezone
from db.queries.queriesPostgres import QueryState, QueryDiff
from rules import Rules
from db.queries.helper import merge_with_past, merge_with_future 
import os
from dotenv import load_dotenv
import json
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
            self.conn.adapters.register_dumper(str, pg.types.string.StrDumperVarchar)

            #CREATE STATE AND DIFF TABLE, IF THEY DON'T EXIST
            await self.create_state_customers_table()
            #self.create_diff_customers_table()

        except Exception as error:
            print(f"Error occurred: {error}")

##########################BOTH STATE AND DIFF FUNCTIONS###########################################


##########################STATE BASED FUNCTIONS#################################################

    async def create_state_customers_table(self):
            query = QueryState.CREATE_TABLE

            async with self.conn.cursor() as cur:
                await cur.execute(query)
                print("Customer table exists.")

    async def update_user_state(self, profile: UserProfile):

            if self.conn is None:
                raise Exception("Database connection not established")

            dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
            id = profile.userId
            attributes = profile.attributes

            params = (id, dt)

            if not attributes:
                return profile
            
            #1. Get most recent valid attributes
            past = {}

            async with self.conn.cursor() as cur:
                query = QueryState.SELECT_USER_AT
                await cur.execute(query, params)
                row = await cur.fetchone()
                if row:
                    past = row['attributes']


            #2. Update attributes for given time
            print(attributes, type(attributes))
            print(past, type(past))

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

            #5. Update all future states
            for future in futures:
                future = merge_with_future(future, attributes, self.rules)

                print(future["at"])

                params_w_attr = (id, Jsonb(future["attributes"]), future["at"])

                query = QueryState.INSERT_WITH_TIME
                async with self.conn.cursor() as cur:
                    await cur.execute(query, params_w_attr)
            
            
            return profile
    

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")
        

        if timestamp: 
            query = QueryState.SELECT_USER_AT
            
            dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc) #ms to seconds
            params = (userId, dt)
        else:

            query = QueryState.SELECT_USER

            params = (userId,)
        
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            if row:
                return UserProfile(userId=row['id'], attributes=row['attributes'], timestamp=int(row['at'].timestamp()))
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
    
# TODO