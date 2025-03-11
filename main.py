from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models import UserProfile, Attributes
from db.in_memory import InMemoryDB
from db.XTDB import XTDB
from db.terminusDB import terminusDB
from typing import Optional, List
from config import config

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

@app.put("/users/{user_id}")
async def update_user(user_id: str, attributes: Attributes):
    """Update or insert a user profile."""
    profile = UserProfile(user_id=user_id, attributes=attributes.attributes, timestamp=attributes.timestamp)
    profile = await db.update_user(profile)
    return {"message": "Profile updated successfully!", "user_id": user_id, "timestamp": profile.timestamp}

@app.get("/users/all")
async def get_all_users():
    """Retrieve the latest or specific version of a user profile."""

    #await db.get_all_triples() #debug for terminus
    
    docs = await db.get_all_documents()
    
    if not docs:
        raise HTTPException(status_code=404, detail="No user found")
    return docs


@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str, timestamp: Optional[int] = None):
    """Retrieve the latest or specific version of a user profile."""
    profile = await db.get_user(user_id, timestamp)
    if not profile:
        raise HTTPException(status_code=404, detail="No user found")
    return profile