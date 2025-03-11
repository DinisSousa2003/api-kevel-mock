from abc import ABC, abstractmethod
from models import UserProfile
from typing import Optional, Dict

class Database(ABC):
    @abstractmethod
    async def update_user(self, user: UserProfile) -> None:
        pass

    @abstractmethod
    async def get_user(self, userId: str, timestamp: Optional[int] = None) -> Optional[UserProfile]:
        pass
