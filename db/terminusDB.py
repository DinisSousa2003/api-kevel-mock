from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
from datetime import datetime, timezone
from rules import Rules
from terminusdb_client import Client
from terminusdb_client import WOQLQuery as wq
import pprint as pp
from db.schema_maker_terminus import MySchema
import uuid

class terminusDB(Database):

    def __init__(self, db_url):
        self.db_url = db_url
        self.client = None
        self.rules = Rules()
        self.schema = None

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "scheme": parsed_url.scheme,
            "client": parsed_url.netloc,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
        }

        print(f"Connecting to: {DB_PARAMS['scheme']}://{DB_PARAMS['client']}", f"{DB_PARAMS['dbname']}")

        self.schema = MySchema(rules=self.rules.get_all_rules())

        try:
            self.client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.client.connect(key="root", team="admin", user="admin", db=DB_PARAMS["dbname"])
            print("Connected successfully.")

            self.client.optimize('admin/terminus') # optimise database branch (here main)
            self.client.optimize('admin/terminus/_meta') # optimise the repository graph (actually creates a squashed flat layer)
            self.client.optimize('admin/terminus/local/_commits') # commit graph is optimised

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

        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        id = "Customer" + "/" + profile.userId
        attributes = profile.attributes

        if not attributes:
            return profile
        
        #1. Get the most recent valid attributes (assume updates are in order)
        current_attributes = {}
        doc = None
        try:
            doc = self.client.get_document(id)
            if doc:
                current_attributes = doc["attributes"]
        except:
            #print("No current document")
            pass

        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["at"] = dt

        new_attributes = current_attributes

        #2. Update attributes for given time
        for (attr, value) in attributes.items():
            rule = self.rules.get_rule_by_atrr(attr)

             #More recent than past
            if rule == "most-recent":
                new_attributes[attr] = value

            #If exists, is older, else update
            elif rule == "older":
                new_attributes[attr] = current_attributes.get(attr, value)
                
            #Get value and sum
            elif rule == "sum":
                new_attributes[attr] = current_attributes.get(attr, 0) + value

            #Update if value > current
            elif rule == "max":
                new_attributes[attr] = max(current_attributes.get(attr, float('-inf')), value)

            elif rule == "or":
                new_attributes[attr] = value or new_attributes.get(attr, False)

        new_doc["attributes"] = new_attributes
    
        if doc:
            self.client.update_document(new_doc)
            return profile

        #Insert into TerminusDB    
        self.client.insert_document(new_doc)
        return profile
        

    async def get_user_state(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:

        if self.client is None:
            raise Exception("Database connection not established")

        if timestamp:
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) #assuming it is in seconds
        id = "Customer" + "/" + userId

        try: 
            doc = self.client.get_document(id)
            if doc:
                #Use the user id without the customer
                doc["userId"] = userId

                #Remove the not key/value created by terminus
                doc["attributes"].pop("@id", None)
                doc["attributes"].pop("@type", None)
                return UserProfile(**doc)
        except:
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
        
        dt = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        userId = profile.userId
        attributes = profile.attributes
        id = "Customer" + "/" + str(uuid.uuid4())

        #Filter bounded-last-unique attributes
        ignore = self.rules.get_rules_by_type("bounded-last-unique-concatenation.100")
        for (name, _) in ignore.items():
            attributes.pop(name, None)


        new_doc = {}
        new_doc["@id"] = id
        new_doc["@type"] = "Customer"
        new_doc["userId"] = userId
        new_doc["at"] = dt
        new_doc["attributes"] = attributes

        self.client.insert_document(new_doc)

        return profile


    async def get_user_diff(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        if self.client is None:
            raise Exception("Database connection not established")
        
        if timestamp: 
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) #assuming it is in seconds
        
        #1. Select all diffs where userId = userId

        query = {"@type": "Customer", "userId": userId}
        diffs = self.client.query_document(query, as_list=True)
        
        diffs.sort(key=lambda doc: doc["at"])

        if not diffs:
            return None

        #2. Go trough the attributes and merge them, from older to most recent
        attributes = {}
        for diff in diffs:

            #Remove the not key/value created by terminus
            diff["attributes"].pop("@id", None)
            diff["attributes"].pop("@type", None)

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

        #3. <Optional> Merge all updates that are older than x / more than y and cache (faster restore next time)

        #4. Return as user profile
        latest_timestamp = diffs[-1]["at"]  # Last applied timestamp
        dt = datetime.strptime(latest_timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return UserProfile(userId=userId, attributes=attributes, timestamp=int(dt.timestamp()))
    
    async def get_all_triples(self):
        pp.pprint(wq().star().execute(self.client))
        return