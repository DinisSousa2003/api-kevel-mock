from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models import UserProfile
from db.in_memory import InMemoryDB
from db.XTDB import XTDB
from db.terminusDB import terminusDB
from typing import Optional
from config import config
from time import sleep
from datetime import datetime
import json

db = None

@asynccontextmanager
async def startup(app: FastAPI):
    """Initialize database connection at app startup."""
    global db

    if config.DEBUG:
        db = InMemoryDB()
        yield
        #db.clear()
    elif config.DATABASE_NAME == "XTDB":
        db = XTDB(config.DATABASE_URL)
        await db.connect()
        yield
        #db.clear()
    elif config.DATABASE_NAME == "TERMINUSDB":
        db = terminusDB(config.DATABASE_URL)
        await db.connect()  
        yield

app = FastAPI(lifespan=startup)

@app.post("/populate/state")
async def populate_from_file_state(n: int = 0, u: int = 100):
    """Update db from reading file data
    n: number of files
    u: number of users/updates per file"""

    num = 0
    ids = set()

    for i in range(0, n+1):
        print("Reading file", i)

        #with open(f'dataset/updates-{i}.jsonl', "r") as updates:
        with open(f'dataset/small-test.jsonl', "r") as updates:
                for line in updates:
                        payload = json.loads(line.strip())  # Convert JSON string to dictionary
                        profile = UserProfile(**payload)
                        ids.add(profile.userId)

                        profile = await db.update_user_state(profile)

                        num += 1
                        if num % (u/10) == 0:
                            print(num)
                        if num % u == 0:
                            break

    return {"message": f"Performed {num} updates to user profiles", "ids": ids}

@app.post("/populate/diff")
async def populate_from_file_diff(n: int = 0, u: int = 100):
    """Update db from reading file data
    n: number of files
    u: number of users/updates per file"""

    num = 0
    ids = set()
    
    for i in range(0, n+1):
        print("Reading file", i)

        #with open(f'dataset/updates-{i}.jsonl', "r") as updates:
        with open(f'dataset/small-test.jsonl', "r") as updates:
                for line in updates:
                        payload = json.loads(line.strip())  # Convert JSON string to dictionary
                        profile = UserProfile(**payload)
                        ids.add(profile.userId)

                        profile = await db.update_user_diff(profile)

                        num += 1
                        if num % (u/10) == 0:
                            print(num)
                        if num % u == 0:
                            break

    return {"message": f"Performed {num} updates to user profiles", "ids": ids}

@app.delete("/users")
async def delete_all():
     """Delete all data from customer table"""

     await db.erase_all()
     return {"message": "All customers deleted successfully"}

@app.patch("/users/state")
async def update_user(profile: UserProfile):
    """Update or insert a user profile."""

    profile = await db.update_user_state(profile)
    return {"message": "Profile updated successfully!", "userId": profile.userId, "timestamp": datetime.fromtimestamp(profile.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}

@app.patch("/users/diff")
async def update_user(profile: UserProfile):
    """Update or insert a user profile."""

    profile = await db.update_user_diff(profile)
    return {"message": "Profile updated successfully!", "userId": profile.userId, "timestamp": datetime.fromtimestamp(profile.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}

@app.get("/users/state/all")
async def get_all_users():
    """Retrieve the latest or specific version of a user profile."""

    docs = await db.get_all_users_state()
    
    if not docs:
        raise HTTPException(status_code=404, detail="No user found")
    return docs

@app.get("/users/diff/all")
async def get_all_users():
    """Retrieve the latest or specific version of a user profile."""

    #await db.get_all_triples() #debug for terminus
    
    docs = await db.get_all_users_diff()
    
    if not docs:
        raise HTTPException(status_code=404, detail="No user found")
    return docs


@app.get("/users/state/{userId}", response_model=UserProfile)
async def get_user(userId: str, timestamp: Optional[int] = None):
    """Retrieve the latest or specific version of a user profile."""
    profile = await db.get_user_state(userId, timestamp)
    if not profile:
        raise HTTPException(status_code=404, detail="No user found")
    return profile

@app.get("/users/diff/{userId}", response_model=UserProfile)
async def get_user(userId: str, timestamp: Optional[int] = None):
    """Retrieve the latest or specific version of a user profile."""
    profile = await db.get_user_diff(userId, timestamp)
    if not profile:
        raise HTTPException(status_code=404, detail="No user found")
    return profile