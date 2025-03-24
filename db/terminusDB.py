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

        self.schema = MySchema(rules=self.rules.get_all_rules_name())
        #print(self.schema.get_schema())  

        try:
            self.client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.client.connect(key="root", team="admin", user="admin", db=DB_PARAMS["dbname"])
            print("Connected successfully.")

            self.schema.post_schema()

        except Exception as error:
            print(f"Error occurred: {error}")


    async def erase_all(self):
        docs = self.client.get_all_documents()
        for doc in docs:
            self.client.delete_document(doc["@id"])
            #print(f"Deleted document with ID: {doc['@id']}")



    async def update_user(self, profile: UserProfile):

        if self.client is None:
            raise Exception("Database connection not established")

        timestamp = datetime.fromtimestamp(profile.timestamp/1000, tz=timezone.utc) #ms to seconds
        id = profile.userId
        params = (timestamp, id)
        params2 = (id, timestamp)

        # Convert Pydantic model to a WOQLSchema document
        #doc = self.schema.import_objects(**profile.model_dump())  #Uncomment if schema is added

        attributes_to_update = list(profile.attributes.keys())  # Extract attribute names

        if not attributes_to_update:
            return profile
        
        current_values = {}
        doc = None
        try:
            doc = self.client.get_document("JSONDocument" + "/" + id)
            if doc:
                current_values = doc["attributes"]
        except:
            print("No current document")
            pass

        new_attributes = Attributes(attributes=current_values)
        attributes_dict = new_attributes._to_dict()

        new_doc = {}
        new_doc["@id"] = new_doc["@id"] = "JSONDocument" + "/" + id
        new_doc["@type"] = "Customer"
        attributes_dict["@type"] = "Attributes"
        new_doc["attributes"] = attributes_dict
        new_doc["_valid_from"] = timestamp

        for (attr, value) in profile.attributes.items():
            rule = self.rules.get_rule_by_atrr(attr)

            #print(attr, value, rule)

            #TODO: FOR NOW, ASSUME UPDATES COME IN ORDER

            if rule == "most-recent":
                new_doc["attributes"][attr] = value
                
            elif rule == "sum":
                new_doc["attributes"][attr] = (current_values.get(attr) or 0) + value


        print(new_doc)
    
        if doc:
            self.client.update_document(new_doc)
            return profile

        #Insert into TerminusDB    
        self.client.insert_document(new_doc)
        return profile
        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        try: 
            doc = self.client.get_document("JSONDocument" + "/" + userId)
            if doc:
                doc["userId"] = userId
                return UserProfile(**doc)
        except:
            return None
    
    async def get_all_documents(self):
        docs = self.client.get_all_documents()
        return docs
    
    async def get_all_triples(self):
        pp.pprint(wq().star().execute(self.client))
        return