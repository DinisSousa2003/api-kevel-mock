####
# This is the script for storing the schema of your TerminusDB
# database for your project.
# Use 'terminusdb commit' to commit changes to the database and
# use 'terminusdb sync' to change this file according to
# the exsisting database schema
####

###FOR NOW SCHEMALESS, COULD NOT MAKE THE SCHEMA WORK
"""
Title: This is the schema
Description: Terminus Customer Schema
"""
from terminusdb_client.woqlschema import DocumentTemplate
from typing import Any, Optional, List, Union

class Attribute(DocumentTemplate):
    """Key-Value Attribute Store

    Attributes
    ----------
    key: str
    value: Any
    """
    _subdocument = []
    key: str
    value: Union[str, int, bool, float]  # Replace Any with explicit types

class UserProfileSchema(DocumentTemplate):
    """User Profile

    Attributes
    ----------
    userId: str
    attributes: list with attributes
    timestamp: unix_timestamp
    """
    userId: str
    attributes: Optional[List["Attribute"]]  # Key-value store for user attributes
    timestamp: int  # Unix timestamp (optional)

