"""
SHAP Explainability Service for RiskGuard.
Exposes precomputed SHAP explanation profiles and calculates on-the-fly feature attributions.
"""

from typing import Dict, Any, Optional, List
import os
import pandas as pd
import numpy as np

from backend.models_loader import (
    get_model,
    get_preprocessor,
    get_explainer,
    get_feature_names,
    get_precomputed_explanations_dict,
    get_precomputed_predictions_df,
    build_feature_dataframe,
    PROJECT_ROOT
)
from src.explainability.shap_analysis import explain_single_project


def get_project_shap_explanation(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve SHAP explanation for a project by ID.
    Checks precomputed cache first; falls back to on-the-fly calculation if full record is in master.
    """
    explanations = get_precomputed_explanations_dict()
    pid_str = str(project_id)

    if pid_str in explanations:
        return explanations[pid_str]

    # If not in precomputed json, look up in master dataset and compute live
    df_pred = get_precomputed_predictions_df()
    if not df_pred.empty:
        match = df_pred[df_pred["project_id"] == pid_str]
        if not match.empty:
            record = match.iloc[0].to_dict()
            return compute_live_shap_explanation(record)

    return None


def compute_live_shap_explanation(project_data: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
    """
    Compute real-time SHAP explanation for an arbitrary custom project payload.
    """
    model = get_model()
    preprocessor = get_preprocessor()
    explainer = get_explainer()
    feature_names = get_feature_names()

    # Build full record with domain defaults
    df_full = build_feature_dataframe(project_data)
    record = df_full.iloc[0].to_dict()

    explanation = explain_single_project(
        project_record=record,
        model=model,
        preprocessor=preprocessor,
        explainer=explainer,
        feature_names=feature_names,
        top_n=top_n
    )

    return explanation


def get_global_feature_importance(top_n: int = 15) -> List[Dict[str, Any]]:
    """Retrieve top global features ranked by mean absolute SHAP value."""
    csv_path = os.path.join(PROJECT_ROOT, "docs", "reports", "shap", "global_feature_importance.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df.head(top_n).to_dict(orient="records")
    return []
