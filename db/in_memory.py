from models import UserProfile
from typing import Optional, Dict
from db.database import Database
import time

class InMemoryDB(Database):
    def __init__(self):
        self.store = {}

    async def update_user(self, profile: UserProfile):
        #For now doing a LWW merge
        if not profile.timestamp: 
            profile.timestamp = int(time.time())

        old_profile = self.store.get(profile.userId)

        if old_profile:
            if old_profile.timestamp > profile.timestamp:
                return old_profile
            
        self.store[profile.userId] = profile
        return profile

        

    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        profile = self.store.get(userId)
        
        if profile and timestamp:
            if profile.timestamp <= timestamp:
                return profile
            return None  # Simulate versioning check
        
        return profile