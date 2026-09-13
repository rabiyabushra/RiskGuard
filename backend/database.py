"""
MongoDB connection and collection management for RiskGuard.
Uses motor.motor_asyncio for asynchronous non-blocking queries,
with intelligent graceful fallback if the database server is not reachable.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "riskguard_db")

client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo():
    """Initializes async MongoDB connection pool on startup."""
    global client, database
    try:
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000
        )
        # Verify connection by pinging
        await client.admin.command("ping")
        database = client[DATABASE_NAME]
        print(f"[Database] Connected to MongoDB at {MONGO_URI}, db='{DATABASE_NAME}'")
    except Exception as e:
        print(f"[Database] MongoDB offline or unreachable ({e}). Operating in memory/file fallback mode.")
        client = None
        database = None


async def close_mongo_connection():
    """Cleanly terminates MongoDB connections on shutdown."""
    global client, database
    if client:
        client.close()
        print("[Database] MongoDB connection closed.")
        client = None
        database = None


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Returns database instance if connected, else None."""
    return database


def is_mongo_connected() -> bool:
    """Returns True if live MongoDB connection is active."""
    return database is not None


def get_projects_collection():
    """Returns the projects collection if connected."""
    return database["projects"] if database is not None else None


def get_predictions_collection():
    """Returns the predictions collection if connected."""
    return database["predictions"] if database is not None else None


def get_explanations_collection():
    """Returns the explanations collection if connected."""
    return database["explanations"] if database is not None else None