from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserProfile(BaseModel):
    userId: str
    attributes: Dict[str, Any]  # Key-value store for user attributes
    timestamp: Optional[int] = None  # Unix timestamp (optional)


class Attributes(BaseModel):
    attributes: Dict[str, Any]  # Key-value store for user attributes
    timestamp: Optional[int] = None  # Unix timestamp (optional)