import json
import os
from terminusdb_client import WOQLClient
from rules import Rules
import requests
import json
from requests.auth import HTTPBasicAuth

#For schema migration related issues consult:
#https://terminusdb.com/docs/openapi/
#https://terminusdb.com/docs/schema-migration-reference-guide/

class MySchema:
    schema = {}

    def __init__(self, rules): 
        self.schema = {
            "author": "admin",
            "message": "updating schema",
            "operations": [
                { 
                    "@type": "DeleteClass",
                    "class": "Stub"
                },
                {
            
                    "@type": "CreateClass",
                    "class_document":
                    {
                        "@id": "Attributes",
                        "@type": "Class",
                        "@key": 
                        {
                            "@type": "Random"
                        },
                        "@subdocument": []
                    }
                }
                ,
                {
                    "@type": "CreateClass",
                    "class_document":
                    {
                        "@id": "Customer",
                        "@type": "Class",
                        "userId": "xsd:string",
                        "attributes": "Attributes",
                        "_valid_from": "xsd:dateTime"
                    }
                }
            ]
        }


        #print(self.schema)

        #TODO: FOR DIFFERENT TYPES OF RULES MIGHT HAVE TO HAVE A DIFFERENT TYPE
        for rule in rules:
            self.schema["operations"][1]["class_document"][rule] = "xsd:integer"

    def get_schema(self):
        return self.schema
    
    def post_schema(self):
        url = "http://127.0.0.1:6363/api/migration/admin/terminus"
        headers = {
        'Content-Type': 'application/json'
        }
        payload = json.dumps(self.get_schema())
        username = os.getenv("TERMINUS_USER")
        password = os.getenv("TERMINUS_KEY")

        response = requests.request("POST", url, headers=headers, data=payload, auth=HTTPBasicAuth(username, password))
        print(response.text)
