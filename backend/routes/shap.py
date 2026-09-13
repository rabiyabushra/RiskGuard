"""
SHAP Explainability Router for RiskGuard API.
Exposes project-level feature attributions, positive/negative risk drivers, and global importances.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from backend.schemas import SHAPExplanationResponse, ProjectInputSchema
from backend.services.shap_service import (
    get_project_shap_explanation,
    compute_live_shap_explanation,
    get_global_feature_importance
)

router = APIRouter(tags=["Explainability (SHAP)"])


@router.get("/shap/global", response_model=List[Dict[str, Any]])
async def get_global_importance(top_n: int = 15):
    """
    Retrieve top global delay drivers ranked by mean absolute SHAP value across the evaluation set.
    """
    return get_global_feature_importance(top_n=top_n)


@router.get("/projects/{project_id}/explanation", response_model=SHAPExplanationResponse)
@router.get("/shap/{project_id}", response_model=SHAPExplanationResponse)
async def get_project_explanation(project_id: str):
    """
    Retrieve mathematically grounded SHAP feature attributions and narrative explanations for a project.
    """
    explanation = get_project_shap_explanation(project_id)
    if not explanation:
        raise HTTPException(status_code=404, detail=f"Explanation profile not found for project ID '{project_id}'.")
    return explanation


@router.post("/shap/explain", response_model=SHAPExplanationResponse)
async def explain_custom_project(payload: ProjectInputSchema, top_n: int = 5):
    """
    Compute real-time SHAP attributions and human-readable narrative text for a custom project payload.
    """
    try:
        data = payload.model_dump(exclude_none=True)
        explanation = compute_live_shap_explanation(data, top_n=top_n)
        return explanation
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Explainability service is unavailable because model artifacts are missing.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate SHAP explanation.")
