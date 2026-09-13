"""
RiskGuard Backend - FastAPI Application
Member 5's responsibility: Backend & Gemini Integration

This is the entry point for the backend server. It:
- Serves REST APIs for the frontend
- Connects to MongoDB to read/write project data
- Will later integrate the ML model (from Pair 2) and Gemini API for recommendations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import google.generativeai as genai

from database import connect_to_mongo, close_mongo_connection, get_database

# ---------------------------------------------------------
# App setup
# ---------------------------------------------------------
app = FastAPI(
    title="RiskGuard API",
    description="AI-Powered Infrastructure Project Delay Prediction and Risk Assessment System",
    version="0.1.0",
)

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Startup / Shutdown events - connect to MongoDB
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()


# ---------------------------------------------------------
# Basic health-check endpoints
# ---------------------------------------------------------
@app.get("/")
async def root():
    """Simple endpoint to confirm the API is running."""
    return {"message": "RiskGuard API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    """Used to verify the server + DB connection are alive."""
    db = get_database()
    db_status = "connected" if db is not None else "not connected"
    return {"status": "ok", "database": db_status}


# ---------------------------------------------------------
# Example data model for a project
# (Coordinate with Member 2 / Pair 1 on the real schema)
# ---------------------------------------------------------
class Project(BaseModel):
    name: str
    sector: str
    state: str
    district: Optional[str] = None
    cost: Optional[float] = None
    physical_progress: Optional[float] = None  # percentage
    planned_completion: Optional[str] = None   # date as string for now
    revised_completion: Optional[str] = None


# ---------------------------------------------------------
# Project endpoints (talks to MongoDB)
# ---------------------------------------------------------
@app.get("/projects")
async def list_projects(limit: int = 20):
    """Return a list of projects stored in MongoDB."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    projects_cursor = db["projects"].find().limit(limit)
    projects = []
    async for doc in projects_cursor:
        doc["_id"] = str(doc["_id"])  # convert ObjectId to string for JSON
        projects.append(doc)
    return {"count": len(projects), "projects": projects}


@app.post("/projects")
async def create_project(project: Project):
    """Add a new project to MongoDB."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db["projects"].insert_one(project.dict())
    return {"message": "Project created", "id": str(result.inserted_id)}


# ---------------------------------------------------------
# Placeholder for ML prediction endpoint
# (To be filled in once Member 3's trained model is available)
# ---------------------------------------------------------
@app.post("/predict")
async def predict_delay(project: Project):
    """
    Placeholder endpoint: will eventually load the trained model
    (from Pair 2) and return a delay probability + risk category.
    """
    # TODO: Replace this dummy logic with the real model prediction
    dummy_probability = 0.42
    dummy_risk = "Medium"

    return {
        "project_name": project.name,
        "delay_probability": dummy_probability,
        "risk_category": dummy_risk,
        "note": "This is placeholder logic. Real model integration pending from Pair 2.",
    }


# ---------------------------------------------------------
# Gemini recommendation endpoint
# ---------------------------------------------------------
@app.post("/recommendations")
async def get_recommendations(project: Project):
    """
    Calls the Gemini API with project details to generate a
    plain-English recommendation to reduce delay risk.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        return {
            "note": "GEMINI_API_KEY not set yet. Add it to your .env file to enable real recommendations.",
        }

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")

    prompt = (
        f"You are an infrastructure project risk advisor. "
        f"Project name: {project.name}. Sector: {project.sector}. "
        f"State: {project.state}. District: {project.district}. "
        f"Give 2-3 short, actionable recommendations to reduce the risk of delay "
        f"for this project, in plain language."
    )

    try:
        response = model.generate_content(prompt)
        return {"project_name": project.name, "recommendation": response.text}
    except Exception as e:
        return {"error": f"Gemini API call failed: {str(e)}"}