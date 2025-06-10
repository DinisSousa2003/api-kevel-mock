import os
import psycopg as pg
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from imports.models import UserProfile
from imports.test_helper import GetType, PutType
from imports.rules import Rules
from db.queries.queriesXTDB import QueryState, QueryDiff
from db.database import Database
from db.queries.helper import get_size_script, merge_with_past, merge_with_future
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse 
from typing import Optional

class XTDB(Database):

    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None  # Will hold the connection
        self.rules = Rules().get_all_rules()

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
            "user": parsed_url.username,
        }

        print(f"Connecting to: {DB_PARAMS['host']}://{DB_PARAMS['port']}", f"{DB_PARAMS['dbname']}")

        try:
            self.conn = await pg.AsyncConnection.connect(**DB_PARAMS, row_factory=dict_row, autocommit=True, prepare_threshold=None)
            print("Connected to XTDB database successfully.")
            self.conn.adapters.register_dumper(str, pg.types.string.StrDumperVarchar)

        except Exception as error:
            print(f"Error occurred: {error}")


##########################SAME FOR DIFF AND STATE##############################################
    
    async def erase_all(self):
        query = QueryState.ERASE_ALL
        async with self.conn.cursor() as cur:
            await cur.execute(query)

            query = QueryDiff.ERASE_ALL
            await cur.execute(query)

    async def _execute_query(self, query, params):
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)

    async def _execute_fetchone(self, query, params):
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchone()

    async def _execute_fetchall(self, query, params):
        async with self.conn.cursor() as cur:
            await cur.execute(query, params)
            return await cur.fetchall()
        
    async def check_size(self):
        size_dict = {}

        # TODO: Using size function (NOT WORKING)
        # result = await self._execute_fetchall(QueryState.SELECT_SIZE, ())

        # print(result, type(result))

        docker_sizes = get_size_script("xtdb2")
        size_dict.update(docker_sizes)

        return size_dict

    async def check_size_state(self):
        return await self.check_size()
    
    async def check_size_diff(self):
        return await self.check_size()


##########################STATE BASED FUNCTIONS#################################################

    async def update_user_state(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        id = profile.userId
        attributes = profile.attributes

        if not attributes:
            return (None, PutType.NO_UPDATE)
        
        #1. Get most recent valid attributes
        past = {}
        row = await self._execute_fetchone(QueryState.SELECT_ALL_CURRENT_ATTR_VT, (dt, id))
        if row:
            past = row['attributes']


        #2. Update attributes for given time
        new_attributes = merge_with_past(past, attributes, self.rules)

        
        #3. Get all future states
        futures = await self._execute_fetchall(QueryState.SELECT_USER_BT_VT_AND_NOW, (id, dt))

        #4. Update is not in the past  
        if not futures:
            await self._execute_query(QueryState.INSERT_WITH_TIME, (id, Jsonb(new_attributes), dt))
            return (profile, PutType.MOST_RECENT)

        #4. Update is in the past

        #Update from timestamp to the first _valid_to
        await self._execute_query(
            QueryState.INSERT_WITH_TIME_PERIOD,
            (id, Jsonb(new_attributes), dt, futures[0]['_valid_from'])
        )

        #5. Update all future states
        for future in futures:
            future = merge_with_future(future, attributes, self.rules)

            if future['_valid_to']:
                await self._execute_query(
                    QueryState.INSERT_WITH_TIME_PERIOD,
                    (id, Jsonb(future['attributes']), future['_valid_from'], future['_valid_to'])
                )
            else:
                await self._execute_query(
                    QueryState.INSERT_WITH_TIME,
                    (id, Jsonb(future['attributes']), future['_valid_from'])
                )
        
        return (profile, PutType.PAST)

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.conn is None:
            raise Exception("Database connection not established")
        
        typeResponse = GetType.CURRENT

        if timestamp: 
            query = QueryState.SELECT_USER_WITH_VT
            dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc) #ms to seconds
            params = (dt, userId)
            typeResponse = GetType.TIMESTAMP

        else:
            query = QueryState.SELECT_USER
            params = (userId,)
        
        row = await self._execute_fetchone(query, params)
        if row:
            profile = UserProfile(userId=row['_id'], attributes=row['attributes'], timestamp=int(row['_valid_from'].timestamp()))
            return (profile, typeResponse)
            
        return (None, GetType.NO_USER_AT_TIME)
        
    async def get_all_users_state(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        query = QueryState.SELECT_ALL_VALID_WITH_TIMES
        rows = await self._execute_fetchall(query, ())

        return rows
        

##########################DIFF BASED FUNCTIONS#################################################
            

    async def update_user_diff(self, profile: UserProfile):

        if self.conn is None:
            raise Exception("Database connection not established")

        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        userId = profile.userId
        attributes = profile.attributes
        id = uuid.uuid4()

        query = QueryDiff.INSERT_WITH_TIME
        await self._execute_query(query, (id, userId, Jsonb(attributes), dt))
        
        return (profile, PutType.MOST_RECENT)

    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None):

        if self.conn is None:
            raise Exception("Database connection not established")
        
        typeResponse = GetType.CURRENT

        #1. Select all diffs where userId = userId
        if timestamp: 
            query = QueryDiff.SELECT_DIFFS_USER_UP_TO_VT
            dt = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc) #ms to seconds
            params = (userId, dt)
            typeResponse = GetType.TIMESTAMP

        else:
            query = QueryDiff.SELECT_DIFFS_USER
            params = (userId,)

        diffs = await self._execute_fetchall(query, params)

        if not diffs:
            return (None, GetType.NO_USER_AT_TIME)
        
        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:
            attributes = merge_with_past(attributes, diff["attributes"], self.rules)

        #3. <Optional> Merge all updates that are older than x / more than y and cache (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["_valid_from"]  # Last applied timestamp
        profile = UserProfile(userId=userId, attributes=attributes, timestamp=int(latest_timestamp.timestamp()))
        return (profile, typeResponse)
        
    async def get_all_users_diff(self):
         
        if self.conn is None:
            raise Exception("Database connection not established")

        #1. Select all diffs for all the users
        #query = QueryDiff.SELECT_ALL_DIFFS
        query = QueryDiff.SELECT_ALL_USERS

        #TODO: THIS IS IN THE FORMAT [{userId: idOne}, {userId: idTwo}, ....]
        results = await self._execute_fetchall(query)

        print(results)

        """
        # 2. Group diffs by userId
        user_diffs = defaultdict(list)
        for diff in results: 
            user_diffs[diff["userId"]].append(diff)

        #3. Perform the get_user_diff for each user
        user_profiles = {}

        for userId, user_diffs_list in user_diffs:"
        """
