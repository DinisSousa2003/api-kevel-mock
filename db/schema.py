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
