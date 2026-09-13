"""Prediction interface for RiskGuard infrastructure delay risk assessment.

Loads champion model and preprocessing pipeline to provide real-time inference
on individual or batch project data.
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

# Global cache for persisted artifacts
_MODEL = None
_PREPROCESSOR = None

def get_artifacts(models_dir: str = None):
    """Lazy-load the champion model and preprocessor artifacts."""
    global _MODEL, _PREPROCESSOR
    if _MODEL is None or _PREPROCESSOR is None:
        if models_dir is None:
            # Default to relative models/ directory
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

def predict_project(project_data: Union[Dict[str, Any], pd.DataFrame], models_dir: str = None) -> Dict[str, Any]:
    """
    Predict delay status and probability for an infrastructure project.

    Parameters:
    -----------
    project_data : dict or pandas DataFrame containing project attributes.
    models_dir : str, optional path to directory containing persisted artifacts.

    Returns:
    --------
    dict:
        {
            "prediction": 1 or 0 (int),
            "delay_probability": float (0.0 to 1.0)
        }
    """
    model, preprocessor = get_artifacts(models_dir)

    if isinstance(project_data, dict):
        df_input = pd.DataFrame([project_data])
    elif isinstance(project_data, pd.DataFrame):
        df_input = project_data.copy()
    else:
        raise ValueError("Input project_data must be a dictionary or a pandas DataFrame.")

    # Drop identifiers and outcome variables if passed
    drop_cols = [
        "project_id", "legacy_ocms_code", "project_name", "agency", "state",
        "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
        "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
        "schedule_delay_days", "target_delayed"
    ]
    df_clean = df_input.drop(columns=[c for c in drop_cols if c in df_input.columns], errors='ignore')

    # Apply preprocessing transformation
    X_trans = preprocessor.transform(df_clean)

    # Predict class and probability
    pred = int(model.predict(X_trans)[0])
    prob = float(model.predict_proba(X_trans)[0, 1])

    return {
        "prediction": pred,
        "delay_probability": round(prob, 4)
    }

if __name__ == "__main__":
    # Self-test using a test record
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.abspath(os.path.join(current_dir, "..", ".."))
    master_file = os.path.join(base, "data", "processed", "master", "riskguard_master.csv")

    df_test = pd.read_csv(master_file, nrows=2)
    sample_record = df_test.iloc[0].to_dict()

    result = predict_project(sample_record)
    print("Self-test inference output:")
    print(result)
