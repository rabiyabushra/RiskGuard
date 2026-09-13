"""
Pydantic data validation and serialization schemas for RiskGuard API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Project Schemas
# ---------------------------------------------------------------------------

class ProjectBase(BaseModel):
    project_id: Optional[str] = None
    project_name: str
    agency: Optional[str] = None
    sector: str
    state: str
    state_std: Optional[str] = None
    original_cost: Optional[float] = None
    revised_cost: Optional[float] = None
    expenditure: Optional[float] = None
    physical_progress: Optional[float] = None
    planned_duration_days: Optional[float] = None


class ProjectInputSchema(BaseModel):
    """Flexible project payload for predictions, allowing partial or full features."""
    project_id: Optional[str] = None
    project_name: Optional[str] = "Custom Project"
    sector: Optional[str] = "Road Transport & Highways"
    agency: Optional[str] = None
    state: Optional[str] = "National"
    state_std: Optional[str] = None
    original_cost: Optional[float] = 100.0
    revised_cost: Optional[float] = 100.0
    expenditure: Optional[float] = 20.0
    physical_progress: Optional[float] = 20.0
    planned_duration_days: Optional[float] = 730.0
    cost_overrun: Optional[float] = 0.0
    cost_overrun_percent: Optional[float] = 0.0
    expenditure_ratio: Optional[float] = 0.20
    is_mega_project: Optional[int] = 0
    has_cost_overrun: Optional[int] = 0
    # Additional raw features may be supplied dynamically
    extra_features: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}


class ProjectListResponse(BaseModel):
    total: int
    page: int
    limit: int
    projects: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Prediction & Risk Schemas
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    project_id: str
    project_name: str
    prediction: int = Field(..., description="Binary delay prediction: 1 = Delayed, 0 = On Time")
    delay_probability: float = Field(..., description="Estimated probability of project delay [0.0 - 1.0]")
    risk_score: float = Field(..., description="Calibrated risk score [0.0 - 100.0]")
    risk_category: str = Field(..., description="LOW, MEDIUM, or HIGH risk category")
    top_risk_factors: Optional[List[str]] = None


class RiskAnalysisResponse(BaseModel):
    project_id: str
    project_name: str
    delay_probability: float
    risk_score: float
    risk_category: str
    thresholds: Dict[str, Any] = {
        "LOW": "< 35.0",
        "MEDIUM": "35.0 - 64.99",
        "HIGH": ">= 65.0"
    }
    top_risk_factors: List[str]
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# SHAP Explainability Schemas
# ---------------------------------------------------------------------------

class SHAPFactor(BaseModel):
    feature: str
    shap_value: float
    feature_value: Optional[float] = None


class SHAPExplanationResponse(BaseModel):
    project_id: str
    project_name: str
    delay_probability: float
    risk_score: float
    risk_category: str
    base_value: float
    top_risk_increasing_factors: List[SHAPFactor]
    top_risk_reducing_factors: List[SHAPFactor]
    narrative_explanations: List[str]


# ---------------------------------------------------------------------------
# Gemini Recommendation Schemas
# ---------------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    project_id: Optional[str] = None
    project_data: Optional[Dict[str, Any]] = None
    custom_context: Optional[str] = None


class RecommendationResponse(BaseModel):
    project_id: str
    project_name: str
    delay_probability: float
    risk_score: float
    risk_category: str
    top_risk_factors: List[str]
    recommendations: List[str]
    model_used: str
    status: str
    notes: Optional[str] = None
