"""Risk scoring, thresholding, and risk category assignment module.

Calculates project delay risk scores [0, 100], assigns calibrated risk categories
(LOW, MEDIUM, HIGH), and formats risk summaries for individual and batch projects.
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

# Global cached artifacts
_MODEL = None
_PREPROCESSOR = None

def get_artifacts(models_dir: str = None):
    """Lazy-load the champion model and preprocessor artifacts."""
    global _MODEL, _PREPROCESSOR
    if _MODEL is None or _PREPROCESSOR is None:
        if models_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "models"))

        model_path = os.path.join(models_dir, "best_model.pkl")
        preprocessor_path = os.path.join(models_dir, "preprocessor.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact not found: {model_path}")
        if not os.path.exists(preprocessor_path):
            raise FileNotFoundError(f"Preprocessor artifact not found: {preprocessor_path}")

        _MODEL = joblib.load(model_path)
        _PREPROCESSOR = joblib.load(preprocessor_path)

    return _MODEL, _PREPROCESSOR

def calculate_risk_score(delay_probability: float) -> float:
    """
    Convert delay probability (0.0 to 1.0) into a user-friendly risk score (0 to 100).
    
    Parameters:
    -----------
    delay_probability : float between 0.0 and 1.0.

    Returns:
    --------
    float: Risk score bounded in [0.0, 100.0].
    """
    if delay_probability is None or np.isnan(delay_probability):
        raise ValueError("delay_probability cannot be None or NaN.")
    
    prob_clamped = max(0.0, min(1.0, float(delay_probability)))
    return round(prob_clamped * 100.0, 2)

def assign_risk_category(risk_score: float) -> str:
    """
    Assign calibrated risk categories based on risk score thresholds.

    Thresholds:
    - LOW:    risk_score < 35.0
    - MEDIUM: 35.0 <= risk_score < 65.0
    - HIGH:   risk_score >= 65.0

    Parameters:
    -----------
    risk_score : float between 0.0 and 100.0.

    Returns:
    --------
    str: 'LOW', 'MEDIUM', or 'HIGH'.
    """
    if risk_score is None or np.isnan(risk_score):
        raise ValueError("risk_score cannot be None or NaN.")

    score = float(risk_score)
    if score < 35.0:
        return "LOW"
    elif score < 65.0:
        return "MEDIUM"
    else:
        return "HIGH"

def generate_project_risk(project_data: Union[Dict[str, Any], pd.DataFrame], models_dir: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive risk assessment for a single project dictionary or row.

    Parameters:
    -----------
    project_data : dict or DataFrame row containing project features.
    models_dir : str, optional path to persisted model directory.

    Returns:
    --------
    dict containing:
        - project_id (if available)
        - prediction (0 or 1)
        - delay_probability (0.0 to 1.0)
        - risk_score (0.0 to 100.0)
        - risk_category ('LOW', 'MEDIUM', 'HIGH')
    """
    model, preprocessor = get_artifacts(models_dir)

    if isinstance(project_data, dict):
        df_input = pd.DataFrame([project_data])
        proj_id = project_data.get("project_id", "Unknown")
        proj_name = project_data.get("project_name", "Unknown")
    elif isinstance(project_data, pd.DataFrame):
        df_input = project_data.copy()
        proj_id = df_input["project_id"].iloc[0] if "project_id" in df_input.columns else "Unknown"
        proj_name = df_input["project_name"].iloc[0] if "project_name" in df_input.columns else "Unknown"
    else:
        raise ValueError("Input project_data must be a dict or pandas DataFrame.")

    drop_cols = [
        "project_id", "legacy_ocms_code", "project_name", "agency", "state",
        "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
        "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
        "schedule_delay_days", "target_delayed"
    ]
    df_features = df_input.drop(columns=[c for c in drop_cols if c in df_input.columns], errors='ignore')

    # Apply preprocessing pipeline
    X_trans = preprocessor.transform(df_features)

    # Inference
    pred = int(model.predict(X_trans)[0])
    prob = float(model.predict_proba(X_trans)[0, 1])
    score = calculate_risk_score(prob)
    category = assign_risk_category(score)

    return {
        "project_id": str(proj_id),
        "project_name": str(proj_name),
        "prediction": pred,
        "delay_probability": round(prob, 4),
        "risk_score": score,
        "risk_category": category
    }

def batch_calculate_risk(df_master: pd.DataFrame, probabilities: np.ndarray) -> pd.DataFrame:
    """
    Append delay_probability, risk_score, and risk_category to a projects DataFrame.

    Parameters:
    -----------
    df_master : pandas DataFrame containing project records.
    probabilities : 1D array of predicted delay probabilities.

    Returns:
    --------
    pandas DataFrame enriched with risk assessment columns.
    """
    df_out = df_master.copy()
    df_out["delay_probability"] = np.round(probabilities, 4)
    df_out["risk_score"] = df_out["delay_probability"].apply(calculate_risk_score)
    df_out["risk_category"] = df_out["risk_score"].apply(assign_risk_category)
    return df_out

if __name__ == "__main__":
    # Self-test
    test_probs = [0.12, 0.45, 0.85]
    for p in test_probs:
        s = calculate_risk_score(p)
        c = assign_risk_category(s)
        print(f"Prob: {p:.2f} -> Score: {s} -> Category: {c}")
