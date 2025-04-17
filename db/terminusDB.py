import time
from typing import Optional
from urllib.parse import urlparse 
from imports.rules import Rules
from imports.models import UserProfile
from imports.test_helper import GetType, PutType
from terminusdb_client import Client
from terminusdb_client import WOQLQuery as wq
from db.database import Database
from db.queries.schema_maker_terminus import MySchema
from db.queries.queriesTerminusDB import TerminusDBAPI
from db.queries.helper import merge_with_past
from requests.auth import HTTPBasicAuth
import uuid
import os
import pprint as pp
from dotenv import load_dotenv

class terminusDB(Database):

    def __init__(self, db_url):

        load_dotenv('../.env')

        self.db_url = db_url
        self.get_client = None
        self.rules = Rules().get_all_rules()
        self.schema = MySchema(rules=self.rules)
        self.db_name = None

        user = os.getenv("USERNAME", "admin")
        key = os.getenv("KEY", "root")
        self.auth = HTTPBasicAuth(user, key)

        self.API = None

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "scheme": parsed_url.scheme,
            "client": parsed_url.netloc,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
        }

        print(f"Connecting to: {DB_PARAMS['scheme']}://{DB_PARAMS['client']}", f"{DB_PARAMS['dbname']}")

        self.db_name = DB_PARAMS['dbname']

        self.API = TerminusDBAPI(self.db_name, self.auth)

        try:
            self.get_client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.get_client.connect(key="root", team="admin", user="admin", db=self.db_name)
            print("Connected successfully.")

            self.get_client.optimize(f'admin/{self.db_name}') # optimise database branch (here main)
            self.get_client.optimize(f'admin/{self.db_name}/_meta') # optimise the repository graph (actually creates a squashed flat layer)
            self.get_client.optimize(f'admin/{self.db_name}/local/_commits') # commit graph is optimised

            self.update_client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.update_client.connect(key="root", team="admin", user="admin", db=self.db_name)
            print("Connected successfully.")

            self.update_client.optimize(f'admin/{self.db_name}') # optimise database branch (here main)
            self.update_client.optimize(f'admin/{self.db_name}/_meta') # optimise the repository graph (actually creates a squashed flat layer)
            self.update_client.optimize(f'admin/{self.db_name}/local/_commits') # commit graph is optimised

            

            #Check if schema has been posted, if not post
            schema = self.API.get_schema()
            if 'Stub' in schema:
                self.schema.post_schema()


        except Exception as error:
            print(f"Error occurred: {error}")

##########################SAME FOR DIFF AND STATE##############################################

    async def erase_all(self):
        if self.get_client is None:
            raise Exception("Database connection not established")

        docs = self.get_client.get_all_documents()
        for doc in docs:
            self.get_client.delete_document(doc["@id"])

##########################STATE BASED FUNCTIONS#################################################

    async def update_user_state(self, profile: UserProfile):

        if self.update_client is None:
            raise Exception("Database connection not established")

        timestamp = profile.timestamp // 1000
        id = "Customer" + "/" + profile.userId
        attributes = profile.attributes

        if timestamp > int(time.time()):
                return (None, PutType.NO_UPDATE)

        if not attributes:
            return (None, PutType.NO_UPDATE)
        
        #1. Get the most recent valid attributes (assume updates are in order)
        past = {}
        doc = None
        if self.update_client.has_doc(id):
            doc = self.update_client.get_document(id)

            if int(doc["at"]) > timestamp:
                return (None, PutType.PAST)
            past = doc["attributes"]

        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["at"] = timestamp

        #2. Update attributes -> in order, always most recent
        new_doc["attributes"] = merge_with_past(past, attributes, self.rules)
    
        if doc:
            self.update_client.update_document(new_doc, commit_msg=timestamp)
            return (profile, PutType.MOST_RECENT)

        self.update_client.insert_document(new_doc, commit_msg=timestamp)
        return (profile, PutType.MOST_RECENT)
        

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.get_client is None:
            raise Exception("Database connection not established")

        id = "Customer" + "/" + userId

        if timestamp:
            timestamp = timestamp // 1000

        #1. Get the current state of the user
        if self.get_client.has_doc(id):
            doc = self.get_client.get_document(id)

            typeResponse = GetType.CURRENT

            #2. If the current state is in the future from the timestamp given, we need to search in the history
            if timestamp and int(doc['at']) > timestamp:
                present_commit = self.get_client._get_current_commit()

                #3. Get the latest commit at timestamp and retrieve the document in that state
                commit = self.API.get_latest_state(id, timestamp)

                if commit:
                    self.get_client.ref = commit
                    doc = self.get_client.get_document(id)
                    self.get_client.ref = present_commit
                    typeResponse = GetType.TIMESTAMP
                else:
                    return (None, GetType.NO_USER_AT_TIME)

            #4. Use the user id without the customer
            doc["userId"] = userId

            #5. Remove the not key/value created by terminus
            doc["attributes"].pop("@id", None)
            doc["attributes"].pop("@type", None)
            profile = UserProfile(**doc)

            return (profile, typeResponse)
        
        else:
            return (None, GetType.NO_USER_AT_TIME)
    
    async def get_all_users_state(self):
        if self.get_client is None:
            raise Exception("Database connection not established")

        docs = self.get_client.get_all_documents()
        return docs
    

##########################DIFF BASED FUNCTIONS#################################################
    
    async def update_user_diff(self, profile: UserProfile):

        if self.get_client is None:
            raise Exception("Database connection not established")
        
        #1. Create a unique identifier for the change
        timestamp = profile.timestamp // 1000
        userId = profile.userId
        attributes = profile.attributes
        id = "Customer" + "/" + str(uuid.uuid4())

        #2. Insert the update
        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["userId"] = userId
        new_doc["at"] = timestamp
        new_doc["attributes"] = attributes

        self.get_client.insert_document(new_doc, commit_msg=timestamp)

        #WHEN INSERTING DIFFS, THERE IS NO DIFFERENCE IN UPDATE
        return (profile, PutType.MOST_RECENT)


    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        if self.get_client is None:
            raise Exception("Database connection not established")
        
        #0. Get now
        typeResponse = GetType.TIMESTAMP

        if timestamp is None:
            typeResponse = GetType.CURRENT
            timestamp = int(time.time())

                
        #1. Select all diffs where userId = userId
        query = self.API.get_users_diff(userId, timestamp)
        result = self.get_client.query(query)

        diffs = None

        if result["bindings"]:
            diffs = result["bindings"]

        if not diffs:
            return (None, GetType.NO_USER_AT_TIME)

        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:

            #Remove the not key/value created by terminus
            diff["attributes"].pop("@id", None)
            diff["attributes"].pop("@type", None)

            attributes = merge_with_past(attributes, diff["attributes"], self.rules)

        #3. <Optional> Merge all updates that are older than x / more than y and cache (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["at"]["@value"]  # Last applied timestamp
        profile = UserProfile(userId=userId, attributes=attributes, timestamp=latest_timestamp)
        return (profile, typeResponse)
    
    async def get_all_triples(self):
        pp.pprint(wq().star().execute(self.get_client))
        return