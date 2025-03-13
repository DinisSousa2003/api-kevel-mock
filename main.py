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

@app.post("/populate/{n}")
async def populate_from_file(n: int):
    """Update db from reading file data"""

    num = 0
    for i in range(0, n+1):
        print("Reading file", i)

        #with open(f'dataset/updates-{i}.jsonl', "r") as updates:
        with open(f'dataset/small-test.jsonl', "r") as updates:
                for line in updates:
                        payload = json.loads(line.strip())  # Convert JSON string to dictionary
                        profile = UserProfile(**payload)

                        profile = await db.update_user(profile)
                        #print("ok")

                        num += 1
                        if num % 1000 == 0:
                             print(num)

    return {"message": f"Performed {num} updates to user profiles"}

@app.delete("/users")
async def delete_all():
     """Delete all data from customer table"""

     await db.erase_all()
     return {"message": "All customers deleted successfully"}

@app.patch("/users")
async def update_user(profile: UserProfile):
    """Update or insert a user profile."""

    profile = await db.update_user(profile)
    return {"message": "Profile updated successfully!", "userId": profile.userId, "timestamp": datetime.fromtimestamp(profile.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}

@app.get("/users/all")
async def get_all_users():
    """Retrieve the latest or specific version of a user profile."""

    #await db.get_all_triples() #debug for terminus
    
    docs = await db.get_all_documents()
    
    if not docs:
        raise HTTPException(status_code=404, detail="No user found")
    return docs


@app.get("/users/{userId}", response_model=UserProfile)
async def get_user(userId: str, timestamp: Optional[int] = None):
    """Retrieve the latest or specific version of a user profile."""
    profile = await db.get_user(userId, timestamp)
    if not profile:
        raise HTTPException(status_code=404, detail="No user found")
    return profile