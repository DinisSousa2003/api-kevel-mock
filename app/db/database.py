from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass