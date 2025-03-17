from terminusdb_client.schema import DocumentTemplate
from typing import Optional
from datetime import datetime

class Attributes(DocumentTemplate):
    _subdocument = []  # Mark as a subdocument
    attributes: dict  # Use `dict` instead of `Dict[str, int]`

class Customer(DocumentTemplate):
    id: str
    attributes: Attributes  # Reference to the subdocument
    valid_time: Optional[datetime]  # Optional timestamp representing valid time
