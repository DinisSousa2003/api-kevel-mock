from abc import ABC, abstractmethod
from imports.models import UserProfile
from typing import Optional, Dict

class Database(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass