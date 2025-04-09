from enum import Enum

class PutType(Enum):
    PAST = 1
    MOST_RECENT = 2

class GetType(Enum):
    CURRENT = 1
    PAST = 2
    NO_USER = 3
    NO_USER_AT_TIME = 4
