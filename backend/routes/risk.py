"""
Risk Analysis Router for RiskGuard API.
Exposes risk scores, calibrated risk categories, and operational thresholds.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from backend.schemas import RiskAnalysisResponse, ProjectInputSchema
from backend.services.risk_service import get_project_risk_by_id, calculate_risk_metrics
from backend.services.ml_service import run_prediction_pipeline

router = APIRouter(prefix="/risk-analysis", tags=["Risk Analysis"])


@router.get("/{project_id}", response_model=RiskAnalysisResponse)
async def get_project_risk(project_id: str):
    """
    Retrieve calibrated risk analysis metrics and category for a specific project.
    """
    risk_info = get_project_risk_by_id(project_id)
    if not risk_info:
        raise HTTPException(status_code=404, detail=f"Risk analysis not found for project ID '{project_id}'.")
    return risk_info


@router.post("", response_model=RiskAnalysisResponse)
async def analyze_project_risk(payload: ProjectInputSchema):
    """
    Perform on-the-fly risk analysis on a newly submitted project payload.
    """
    try:
        data = payload.model_dump(exclude_none=True)
        pred_result = run_prediction_pipeline(data)
        
        return {
            "project_id": pred_result["project_id"],
            "project_name": pred_result["project_name"],
            "delay_probability": pred_result["delay_probability"],
            "risk_score": pred_result["risk_score"],
            "risk_category": pred_result["risk_category"],
            "thresholds": {
                "LOW": "< 35.0",
                "MEDIUM": "35.0 - 64.99",
                "HIGH": ">= 65.0"
            },
            "top_risk_factors": []
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to calculate risk analysis.")
