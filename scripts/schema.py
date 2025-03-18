from terminusdb_client.schema import DocumentTemplate
from typing import Optional
from datetime import datetime

class Attributes(DocumentTemplate):
    _subdocument = []  # Mark as a subdocument
    attributes: dict

class Customer(DocumentTemplate):
    id: str
    attributes: Attributes  # Reference to the subdocument
    _valid_from: Optional[datetime]  # Optional timestamp representing valid time

"""
hoijnet on TerminusDB discord server:
The JSON datatype would enable you to do this, unfortunately there are some bugs that are not yet ironed out in the schemaless JSON handling and I would not recommend using it yet.
We are looking into how to solve them further ahead. For now the recommendation is to define all schema completely."""