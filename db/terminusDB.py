from models import UserProfile
from typing import Optional
from db.database import Database
from urllib.parse import urlparse 
import time
from datetime import datetime, timezone
from terminusdb_client import Client
from terminusdb_client import WOQLQuery as wq
from terminusdb_client.woqlschema import WOQLSchema
import pprint as pp

class terminusDB(Database):

    def __init__(self, db_url):
        self.db_url = db_url
        self.client = None
        self.schema = WOQLSchema()

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "scheme": parsed_url.scheme,
            "client": parsed_url.netloc,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
        }

        try:
            self.client = Client(DB_PARAMS["scheme"] + "://" + DB_PARAMS["client"])
            self.client.connect(db=DB_PARAMS["dbname"])
            #self.schema.from_db(self.client)

            #Populate here 
            
            print("Connected successfully.")

        except Exception as error:
            print(f"Error occurred: {error}")


    async def update_user(self, profile: UserProfile):

        if not profile.timestamp:
            profile.timestamp = int(time.time())

        # Convert Pydantic model to a WOQLSchema document
        doc = self.schema.import_objects(**profile.model_dump())  #Uncomment if schema is added

        # Insert into TerminusDB
        doc = profile.model_dump(exclude="userId")
        doc["@id"] = "JSONDocument" + "/" + profile.userId
        self.client.insert_document(doc, raw_json=True)
        return profile
        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        doc = self.client.get_document("JSONDocument" + "/" + userId)
        if doc:
            doc["userId"] = userId
            return UserProfile(**doc)
        return None
    
    async def get_all_documents(self):
        docs = self.client.get_all_documents()
        return docs
    
    async def get_all_triples(self):
        pp.pprint(wq().star().execute(self.client))
        return