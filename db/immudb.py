from urllib.parse import urlparse
from immudb.client import ImmudbClient, PersistentRootService
from db.database import Database
from rules import Rules
import os
from dotenv import load_dotenv
from models import UserProfile
from typing import Optional

class immudb(Database):

    def __init__(self, db_url):

        load_dotenv('../.env')

        self.db_url = db_url
        self.client = None  # Will hold the connection
        self.rules = Rules().get_all_rules()

        self.user = os.getenv("USERNAME", "immudb")
        self.key = os.getenv("KEY", "immudb")

    def encode(what: str):
        return what.encode("utf-8")

    def decode(what: bytes):
        return what.decode("utf-8")

    async def connect(self):
        parsed_url = urlparse(self.db_url) 

        DB_PARAMS = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "dbname": parsed_url.path.lstrip("/"),  # Extracts database name
        }

        print(f"Connecting to: {DB_PARAMS['host']}:{DB_PARAMS['port']}", f"{DB_PARAMS['dbname']}")

        self.client = ImmudbClient(f"{DB_PARAMS['host']}:{DB_PARAMS['port']}", rs=PersistentRootService())

        self.client.login(username=self.user, password=self.key, database=DB_PARAMS['dbname'])

        #self.test()

##########################BOTH STATE AND DIFF FUNCTIONS###########################################
    
    def test(self):
        key = "Hello".encode('utf8')
        value = "Immutable World!".encode('utf8')

        # set a key/value pair
        self.client.set(key, value)

        # reads back the value
        readback = self.client.get(key)
        saved_value = readback.value.decode('utf8')
        print("Hello", saved_value)

##########################STATE BASED FUNCTIONS#################################################

# TODO

#immudb does not seem to support time-travelling by comparing to an attribute, and so is unsuitable for this purpose
    

##########################DIFF BASED FUNCTIONS#################################################
    
# TODO