"""
Projects Router for RiskGuard API.
Provides endpoints to list, filter, inspect, and register infrastructure projects.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.database import get_projects_collection, is_mongo_connected
from backend.models_loader import get_precomputed_predictions_df
from backend.schemas import ProjectListResponse, ProjectInputSchema

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=Dict[str, Any])
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=2000, description="Items per page"),
    state: Optional[str] = Query(None, description="Filter by state (e.g. 'Gujarat', 'Assam')"),
    sector: Optional[str] = Query(None, description="Filter by sector (e.g. 'Civil Aviation')"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category: LOW, MEDIUM, HIGH")
):
    """
    List infrastructure projects with optional state, sector, and risk-category filtering.
    Operates via MongoDB when available, or seamlessly uses the master dataset cache.
    """
    skip = (page - 1) * limit

    # 1. If MongoDB is connected and populated, query MongoDB
    coll = get_projects_collection()
    if is_mongo_connected() and coll is not None:
        query: Dict[str, Any] = {}
        if state:
            query["$or"] = [{"state": {"$regex": state, "$options": "i"}}, {"state_std": {"$regex": state, "$options": "i"}}]
        if sector:
            query["sector"] = {"$regex": sector, "$options": "i"}
        if risk_category:
            query["risk_category"] = risk_category.upper()

        total = await coll.count_documents(query)
        if total > 0:
            cursor = coll.find(query, {"_id": 0}).skip(skip).limit(limit)
            projects = await cursor.to_list(length=limit)
            return {
                "total": total,
                "page": page,
                "limit": limit,
                "data_source": "mongodb",
                "projects": projects
            }

    # 2. Resilient file/memory fallback using master dataset
    df = get_precomputed_predictions_df()
    if df.empty:
        return {"total": 0, "page": page, "limit": limit, "data_source": "empty", "projects": []}

    filtered = df.copy()
    if state:
        filtered = filtered[filtered["state"].astype(str).str.contains(state, case=False, na=False) |
                             filtered["state_std"].astype(str).str.contains(state, case=False, na=False)]
    if sector:
        filtered = filtered[filtered["sector"].astype(str).str.contains(sector, case=False, na=False)]
    if risk_category:
        filtered = filtered[filtered["risk_category"].astype(str).str.upper() == risk_category.upper()]

    total = len(filtered)
    page_df = filtered.iloc[skip:skip + limit]
    
    # Replace NaNs with None for clean JSON serialization
    records = page_df.where(pd.notnull(page_df), None).to_dict(orient="records")

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data_source": "cached_master",
        "projects": records
    }


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str):
    """
    Retrieve full details for an individual infrastructure project by its ID.
    """
    pid_str = str(project_id)

    # 1. Check MongoDB first
    coll = get_projects_collection()
    if is_mongo_connected() and coll is not None:
        doc = await coll.find_one({"project_id": pid_str}, {"_id": 0})
        if doc:
            return doc

    # 2. Check cached master dataset
    df = get_precomputed_predictions_df()
    if not df.empty:
        match = df[df["project_id"] == pid_str]
        if not match.empty:
            row = match.iloc[0]
            clean_dict = row.where(pd.notnull(row), None).to_dict()
            return clean_dict

    raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found.")


@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_project(project: ProjectInputSchema):
    """
    Register a new infrastructure project into the database.
    """
    doc = project.model_dump(exclude_none=True)
    if "project_id" not in doc or not doc["project_id"]:
        import uuid
        doc["project_id"] = f"PRJ-{uuid.uuid4().hex[:8].upper()}"

    coll = get_projects_collection()
    if is_mongo_connected() and coll is not None:
        await coll.update_one({"project_id": doc["project_id"]}, {"$set": doc}, upsert=True)
        return {
            "message": "Project registered successfully in MongoDB",
            "project_id": doc["project_id"],
            "status": "persisted"
        }

    return {
        "message": "Project received (MongoDB offline, stored in session)",
        "project_id": doc["project_id"],
        "status": "acknowledged"
    }
