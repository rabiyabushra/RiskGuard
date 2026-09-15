"""
Centralized, cached artifact and dataset loader for RiskGuard backend.
Provides thread-safe access to the trained XGBoost model, fitted preprocessor,
SHAP TreeExplainer, and master datasets.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

# Locate project root dynamically
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.explainability.shap_analysis import get_tree_explainer

# Global cached singletons
_MODEL = None
_PREPROCESSOR = None
_EXPLAINER = None
_FEATURE_NAMES = None
_PRECOMPUTED_PREDICTIONS_DF = None
_PRECOMPUTED_EXPLANATIONS_DICT = None
_DEFAULT_FEATURE_ROW = None


def get_model():
    """Retrieve the trained production champion model."""
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(PROJECT_ROOT, "models", "best_model.pkl")
        if not os.path.exists(model_path):
            # Check fallback model artifacts
            for alt_name in ["xgboost.pkl", "random_forest.pkl", "logistic_regression.pkl"]:
                alt_path = os.path.join(PROJECT_ROOT, "models", alt_name)
                if os.path.exists(alt_path):
                    model_path = alt_path
                    break
            else:
                raise FileNotFoundError(f"Model file not found at: {model_path}")
        _MODEL = joblib.load(model_path)
    return _MODEL


def get_preprocessor():
    """Retrieve the fitted preprocessing pipeline."""
    global _PREPROCESSOR
    if _PREPROCESSOR is None:
        prep_path = os.path.join(PROJECT_ROOT, "models", "preprocessor.pkl")
        if not os.path.exists(prep_path):
            alt_joblib = os.path.join(PROJECT_ROOT, "models", "preprocessor.joblib")
            if os.path.exists(alt_joblib):
                prep_path = alt_joblib
            else:
                raise FileNotFoundError(f"Preprocessor file not found at: {prep_path}")
        _PREPROCESSOR = joblib.load(prep_path)
    return _PREPROCESSOR


def get_explainer():
    """Retrieve the SHAP TreeExplainer instance."""
    global _EXPLAINER
    if _EXPLAINER is None:
        model = get_model()
        _EXPLAINER = get_tree_explainer(model)
    return _EXPLAINER


def get_feature_names() -> List[str]:
    """Retrieve list of transformed feature names expected by the model."""
    global _FEATURE_NAMES
    if _FEATURE_NAMES is None:
        x_test_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "X_test.csv")
        if os.path.exists(x_test_path):
            df_x = pd.read_csv(x_test_path, nrows=1)
            _FEATURE_NAMES = list(df_x.columns)
        else:
            # Fallback
            _FEATURE_NAMES = [f"feature_{i}" for i in range(97)]
    return _FEATURE_NAMES


def get_precomputed_predictions_df() -> pd.DataFrame:
    """Retrieve the pre-calculated portfolio predictions dataframe."""
    global _PRECOMPUTED_PREDICTIONS_DF
    if _PRECOMPUTED_PREDICTIONS_DF is None:
        csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "risk_predictions.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df["project_id"] = df["project_id"].astype(str)
            _PRECOMPUTED_PREDICTIONS_DF = df
        else:
            _PRECOMPUTED_PREDICTIONS_DF = pd.DataFrame()
    return _PRECOMPUTED_PREDICTIONS_DF


def get_precomputed_explanations_dict() -> Dict[str, Any]:
    """Retrieve precomputed SHAP explanations indexed by project_id."""
    global _PRECOMPUTED_EXPLANATIONS_DICT
    if _PRECOMPUTED_EXPLANATIONS_DICT is None:
        json_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "project_explanations.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _PRECOMPUTED_EXPLANATIONS_DICT = {str(item["project_id"]): item for item in data}
        else:
            _PRECOMPUTED_EXPLANATIONS_DICT = {}
    return _PRECOMPUTED_EXPLANATIONS_DICT


def get_default_feature_row() -> pd.Series:
    """
    Returns a representative baseline row (median values of numeric columns and mode of categoricals)
    derived from riskguard_master.csv to populate any missing demographic/contextual features
    when custom minimal project payloads are provided.
    """
    global _DEFAULT_FEATURE_ROW
    if _DEFAULT_FEATURE_ROW is None:
        master_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "riskguard_master.csv")
        if os.path.exists(master_path):
            df_m = pd.read_csv(master_path)
            # Take the first representative row as base template
            _DEFAULT_FEATURE_ROW = df_m.iloc[0].to_dict()
        else:
            _DEFAULT_FEATURE_ROW = {}
    return _DEFAULT_FEATURE_ROW.copy()


def build_feature_dataframe(project_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Construct a complete dataframe compatible with the preprocessor,
    filling non-supplied contextual fields with domain defaults.
    """
    base_record = get_default_feature_row()
    
    # Overwrite with user-supplied values
    for k, v in project_dict.items():
        if v is not None and k != "extra_features":
            base_record[k] = v

    if "extra_features" in project_dict and isinstance(project_dict["extra_features"], dict):
        for k, v in project_dict["extra_features"].items():
            base_record[k] = v

    # Ensure financial ratios are synchronized if raw costs given
    orig = float(base_record.get("original_cost", 100.0) or 100.0)
    rev = float(base_record.get("revised_cost", orig) or orig)
    exp = float(base_record.get("expenditure", 0.0) or 0.0)
    prog = float(base_record.get("physical_progress", 0.0) or 0.0)

    base_record["cost_overrun"] = max(0.0, rev - orig)
    base_record["cost_overrun_percent"] = (base_record["cost_overrun"] / orig * 100.0) if orig > 0 else 0.0
    base_record["expenditure_ratio"] = (exp / rev) if rev > 0 else 0.0
    base_record["expenditure_to_original_ratio"] = (exp / orig) if orig > 0 else 0.0
    base_record["progress_to_expenditure_gap"] = prog - (base_record["expenditure_ratio"] * 100.0)
    base_record["is_mega_project"] = 1 if rev >= 1000.0 else 0
    base_record["has_cost_overrun"] = 1 if base_record["cost_overrun"] > 0.0 else 0

    return pd.DataFrame([base_record])
