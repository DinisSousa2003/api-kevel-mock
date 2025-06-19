from enum import Enum

class PutType(Enum):
    PAST = 1
    MOST_RECENT = 2
    NO_UPDATE = 3

class GetType(Enum):
    CURRENT = 1
    TIMESTAMP = 2
    NO_USER_AT_TIME = 3
    PAST = 4