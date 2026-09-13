"""
Risk Analysis Service for RiskGuard.
Directly interfaces with Member 4's calibrated risk scoring and threshold assignment logic.
"""

from typing import Dict, Any, Optional
import sys
import os

from src.explainability.risk_analysis import (
    calculate_risk_score,
    assign_risk_category
)
from backend.models_loader import get_precomputed_predictions_df


def calculate_risk_metrics(delay_probability: float) -> Dict[str, Any]:
    """
    Applies Member 4's exact risk scoring and categorization formulas:
    risk_score = clamp(prob, 0.0, 1.0) * 100
    category = LOW (<35) | MEDIUM (35-65) | HIGH (>=65)
    """
    score = calculate_risk_score(delay_probability)
    category = assign_risk_category(score)
    return {
        "delay_probability": round(float(delay_probability), 4),
        "risk_score": score,
        "risk_category": category,
        "thresholds": {
            "LOW": "< 35.0",
            "MEDIUM": "35.0 - 64.99",
            "HIGH": ">= 65.0"
        }
    }


def get_project_risk_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """Fetch precalculated risk metrics and top risk factors for a project ID."""
    df_pred = get_precomputed_predictions_df()
    if df_pred.empty:
        return None

    match = df_pred[df_pred["project_id"] == str(project_id)]
    if match.empty:
        return None

    row = match.iloc[0]
    top_factors = []
    for col in ["top_risk_factor_1", "top_risk_factor_2", "top_risk_factor_3"]:
        if col in row and pd_not_na(row[col]):
            top_factors.append(str(row[col]))

    return {
        "project_id": str(row["project_id"]),
        "project_name": str(row.get("project_name", "Unknown")),
        "delay_probability": round(float(row.get("delay_probability", 0.0)), 4),
        "risk_score": float(row.get("risk_score", 0.0)),
        "risk_category": str(row.get("risk_category", "MEDIUM")),
        "top_risk_factors": top_factors,
        "thresholds": {
            "LOW": "< 35.0",
            "MEDIUM": "35.0 - 64.99",
            "HIGH": ">= 65.0"
        }
    }


def pd_not_na(val) -> bool:
    """Safe check for NaN/None values."""
    if val is None:
        return False
    try:
        import pandas as pd
        return not pd.isna(val)
    except Exception:
        return True
