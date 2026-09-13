"""
RiskGuard API — Core Application Entrypoint.
AI-Powered Infrastructure Project Delay Prediction and Risk Assessment System.
"""

import os
import sys
from contextlib import asynccontextmanager

# Ensure repository root is on sys.path regardless of launch directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import connect_to_mongo, close_mongo_connection, is_mongo_connected
from backend.models_loader import get_model, get_preprocessor, get_explainer
from backend.routes import (
    projects,
    prediction,
    risk,
    shap,
    recommendations
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup initialization and shutdown resource cleanup."""
    print("[Startup] Initializing RiskGuard backend services...")
    # 1. Connect to MongoDB
    await connect_to_mongo()

    # 2. Warm up model and preprocessing artifacts
    try:
        get_model()
        get_preprocessor()
        print("[Startup] Machine learning models and preprocessor warmed up successfully.")
    except Exception as e:
        print(f"[Startup] Warning: Could not warm up ML models: {e}")

    yield

    # Shutdown
    print("[Shutdown] Releasing database connections...")
    await close_mongo_connection()


app = FastAPI(
    title="RiskGuard API",
    description="Intelligent Infrastructure Delay Risk Assessment, SHAP Explainability & Mitigation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration allowing local development with React / Leaflet UI
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers
app.include_router(projects.router)
app.include_router(prediction.router)
app.include_router(risk.router)
app.include_router(shap.router)
app.include_router(recommendations.router)


@app.get("/", tags=["System"])
async def root():
    """Service status confirmation and API overview."""
    return {
        "service": "RiskGuard API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "modules": [
            "projects",
            "prediction",
            "risk-analysis",
            "shap-explainability",
            "gemini-recommendations"
        ]
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Live health status of API and attached MongoDB instance."""
    mongo_status = "connected" if is_mongo_connected() else "offline (memory/file fallback active)"
    return {
        "status": "healthy",
        "database": mongo_status,
        "model_loaded": get_model() is not None,
        "preprocessor_loaded": get_preprocessor() is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting RiskGuard API on http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)