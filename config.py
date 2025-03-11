import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "http://localhost:3000")  # Default to in-memory DB
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_NAME = os.getenv("DATABASE_NAME", "XTDB")

config = Config()
