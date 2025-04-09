import json
import os
from terminusdb_client import WOQLClient
from imports.rules import Rules
import requests
import json
from requests.auth import HTTPBasicAuth

#For schema migration related issues consult:
#https://terminusdb.com/docs/openapi/
#https://terminusdb.com/docs/schema-migration-reference-guide/

class MySchema:
    schema = {}

    """Schema is the schema for the database.
    If we are using state based, id is user id
    If we are using op-based, id is random and we use user id to get all user updates"""

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
                        "userId": { "@type" : "Optional", "@class" : "xsd:string" },
                        "attributes": "Attributes",
                        "at": "xsd:integer"
                    }
                }
            ]
        }


        #print(self.schema)

        #TODO: FOR DIFFERENT TYPES OF RULES MIGHT HAVE TO HAVE A DIFFERENT TYPE
        for (name, rule) in rules.items():
            if "bounded-last-unique-concatenation" in rule:
                self.schema["operations"][1]["class_document"][name] = { "@type" : "Array", "@class" : "xsd:double" }
            elif rule == "or":
                self.schema["operations"][1]["class_document"][name] = { "@type" : "Optional", "@class" : "xsd:boolean" }
            else:
                self.schema["operations"][1]["class_document"][name] = { "@type" : "Optional", "@class" : "xsd:double" }

    def get_schema(self):
        return self.schema
    
    def post_schema(self):
        url = "http://127.0.0.1:6363/api/migration/admin/terminus"
        headers = {
        'Content-Type': 'application/json'
        }
        payload = json.dumps(self.get_schema())
        username = os.getenv("USERNAME")
        password = os.getenv("KEY")

        response = requests.request("POST", url, headers=headers, data=payload, auth=HTTPBasicAuth(username, password))
        print(response.text)
