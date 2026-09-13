"""
MongoDB connection handling for the RiskGuard backend.

Uses Motor (the async MongoDB driver) so it works cleanly with FastAPI's
async endpoints.

Coordinate with Member 2 on the actual collection names / schema -
"projects" is just a placeholder collection name for now.
"""

from dotenv import load_dotenv
load_dotenv()

import os
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
# Set this in a .env file - never hardcode real credentials.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "riskguard")

# ---------------------------------------------------------
# Module-level client/db handles
# ---------------------------------------------------------
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """Called on app startup - opens the MongoDB connection."""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Trigger a quick check that the server is reachable
        await client.admin.command("ping")
        database = client[DATABASE_NAME]
        print(f"[database] Connected to MongoDB at {MONGO_URI}, db='{DATABASE_NAME}'")
    except Exception as e:
        print(f"[database] Could not connect to MongoDB: {e}")
        print("[database] The API will still run, but DB-dependent endpoints will fail.")
        client = None
        database = None


async def close_mongo_connection():
    """Called on app shutdown - closes the MongoDB connection cleanly."""
    global client
    if client:
        client.close()
        print("[database] MongoDB connection closed")


def get_database():
    """Used by endpoints to access the database instance."""
    return database