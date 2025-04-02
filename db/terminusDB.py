from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
from rules import Rules
from terminusdb_client import Client
from terminusdb_client import WOQLQuery as wq
import pprint as pp
from db.schema_maker_terminus import MySchema
import uuid
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from db.queries.queriesTerminusDB import TerminusDBAPI
from db.queries.helper import merge_with_past

class terminusDB(Database):

    def __init__(self, db_url):

        load_dotenv('../.env')

        self.db_url = db_url
        self.client = None
        self.rules = Rules().get_all_rules()
        self.schema = MySchema(rules=self.rules)
        self.db_name = None

        user = os.getenv("TERMINUS_USER", "admin")
        key = os.getenv("TERMINUS_KEY", "root")
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
            self.client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.client.connect(key="root", team="admin", user="admin", db=self.db_name)
            print("Connected successfully.")

            self.client.optimize(f'admin/{self.db_name}') # optimise database branch (here main)
            self.client.optimize(f'admin/{self.db_name}/_meta') # optimise the repository graph (actually creates a squashed flat layer)
            self.client.optimize(f'admin/{self.db_name}/local/_commits') # commit graph is optimised

            #Check if schema has been posted, if not post
            schema = self.API.get_schema()
            if 'Stub' in schema:
                self.schema.post_schema()


        except Exception as error:
            print(f"Error occurred: {error}")

##########################SAME FOR DIFF AND STATE##############################################

    async def erase_all(self):
        if self.client is None:
            raise Exception("Database connection not established")

        docs = self.client.get_all_documents()
        for doc in docs:
            self.client.delete_document(doc["@id"])

##########################STATE BASED FUNCTIONS#################################################

    async def update_user_state(self, profile: UserProfile):

        if self.client is None:
            raise Exception("Database connection not established")

        timestamp = profile.timestamp
        id = "Customer" + "/" + profile.userId
        attributes = profile.attributes

        if not attributes:
            return profile
        
        #1. Get the most recent valid attributes (assume updates are in order)
        past = {}
        doc = None
        if self.client.has_doc(id):
            doc = self.client.get_document(id)

            if int(doc["at"]) > timestamp:
                print("Ignore updates to the past")
                return profile
            past = doc["attributes"]
        else:
            #print(e)
            print("No document with that id present")
            pass

        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["at"] = timestamp

        #2. Update attributes
        new_doc["attributes"] = merge_with_past(past, attributes, self.rules)
    
        if doc:
            self.client.update_document(new_doc, commit_msg=timestamp)
            return profile

        #Insert into TerminusDB
        self.client.insert_document(new_doc, commit_msg=timestamp)
        return profile
        

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.client is None:
            raise Exception("Database connection not established")

        id = "Customer" + "/" + userId

        if self.client.has_doc(id):
            doc = self.client.get_document(id)

            present_commit = self.client._get_current_commit()

            if timestamp and int(doc['at']) > timestamp:
                commit = self.API.get_latest_state(id, timestamp)

                if commit:
                    self.client.ref = commit
                    doc = self.client.get_document(id)
                    self.client.ref = present_commit
                else:
                    print("No user with that id was found")
                    return None

            #Use the user id without the customer
            doc["userId"] = userId

            #Remove the not key/value created by terminus
            doc["attributes"].pop("@id", None)
            doc["attributes"].pop("@type", None)
            return UserProfile(**doc)
        else:
            print("No user with that id was found")
            return None
    
    async def get_all_users_state(self):
        if self.client is None:
            raise Exception("Database connection not established")

        docs = self.client.get_all_documents()
        return docs
    

##########################DIFF BASED FUNCTIONS#################################################
    
    async def update_user_diff(self, profile: UserProfile):

        if self.client is None:
            raise Exception("Database connection not established")
        
        timestamp = profile.timestamp
        userId = profile.userId
        attributes = profile.attributes
        id = "Customer" + "/" + str(uuid.uuid4())

        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["userId"] = userId
        new_doc["at"] = timestamp
        new_doc["attributes"] = attributes

        self.client.insert_document(new_doc, commit_msg=timestamp)

        return profile


    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        if self.client is None:
            raise Exception("Database connection not established")
                
        #1. Select all diffs where userId = userId
        query = self.API.get_users_diff(userId, timestamp)
        result = self.client.query(query)

        diffs = None

        if result["bindings"]:
            diffs = result["bindings"]
        else:
            print("Cannot find result.")

        if not diffs:
            return None

        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:

            #Remove the not key/value created by terminus
            diff["attributes"].pop("@id", None)
            diff["attributes"].pop("@type", None)

            attributes = merge_with_past(attributes, diff["attributes"], self.rules)

        #3. TODO: <Optional> Merge all updates that are older than x / more than y and cache (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["at"]["@value"]  # Last applied timestamp
        return UserProfile(userId=userId, attributes=attributes, timestamp=latest_timestamp)
    
    async def get_all_triples(self):
        pp.pprint(wq().star().execute(self.client))
        return