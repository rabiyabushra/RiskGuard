"""
Machine Learning Inference Service for RiskGuard.
Integrates trained XGBoost champion model and fitted ColumnTransformer.
"""

from typing import Dict, Any, Optional
import datetime
import pandas as pd
import numpy as np

from backend.models_loader import (
    get_model,
    get_preprocessor,
    build_feature_dataframe
)
from backend.services.risk_service import calculate_risk_metrics
from backend.database import get_predictions_collection


# Non-feature identifiers and target columns to strip before preprocessing
DROP_COLS = [
    "project_id", "legacy_ocms_code", "project_name", "agency", "state",
    "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
    "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
    "schedule_delay_days", "target_delayed"
]


def run_prediction_pipeline(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute end-to-end model inference on raw project data:
    Raw Input -> Feature Enrichment -> Preprocessing -> Model -> Probability -> Risk Score.
    """
    model = get_model()
    preprocessor = get_preprocessor()

    # 1. Build model-compatible dataframe with proper contextual defaults
    df_raw = build_feature_dataframe(project_data)
    
    proj_id = str(project_data.get("project_id", df_raw.get("project_id", ["Unknown"]).iloc[0]))
    proj_name = str(project_data.get("project_name", df_raw.get("project_name", ["Unknown"]).iloc[0]))

    # 2. Strip non-feature columns
    df_features = df_raw.drop(columns=[c for c in DROP_COLS if c in df_raw.columns], errors='ignore')

    # 3. Transform via fitted ColumnTransformer
    X_trans = preprocessor.transform(df_features)

    # 4. Predict probability and binary class
    pred = int(model.predict(X_trans)[0])
    prob = float(model.predict_proba(X_trans)[0, 1])

    # 5. Calculate calibrated risk score & category via Member 4 logic
    risk_info = calculate_risk_metrics(prob)

    result = {
        "project_id": proj_id,
        "project_name": proj_name,
        "prediction": pred,
        "delay_probability": round(prob, 4),
        "risk_score": risk_info["risk_score"],
        "risk_category": risk_info["risk_category"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    return result


async def persist_prediction(prediction_result: Dict[str, Any]):
    """Optionally persist prediction result to MongoDB collection if online."""
    try:
        coll = get_predictions_collection()
        if coll is not None:
            doc = {
                "project_id": prediction_result["project_id"],
                "project_name": prediction_result["project_name"],
                "prediction": prediction_result["prediction"],
                "delay_probability": prediction_result["delay_probability"],
                "risk_score": prediction_result["risk_score"],
                "risk_category": prediction_result["risk_category"],
                "model_version": "v1.0.0-XGBoost",
                "predicted_at": datetime.datetime.now(datetime.timezone.utc)
            }
            await coll.update_one(
                {"project_id": prediction_result["project_id"]},
                {"$set": doc},
                upsert=True
            )
    except Exception as e:
        print(f"[MLService] Warning: Failed to persist prediction to MongoDB: {e}")
