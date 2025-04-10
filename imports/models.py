from pydantic import BaseModel
from typing import Optional, Dict, Any
from imports.test_helper import GetType, PutType

class UserProfile(BaseModel):
    userId: str
    attributes: Dict[str, Any]  # Key-value store for user attributes
    timestamp: Optional[int] = None  # Unix timestamp (optional)

class Attributes(BaseModel):
    attributes: Dict[str, Any]  # Key-value store for user attributes
    timestamp: Optional[int] = None  # Unix timestamp (optional)

class GetResponse(BaseModel):
    profile: UserProfile
    response: GetType

class PutResponse(BaseModel):
    profile: UserProfile
    response: PutType