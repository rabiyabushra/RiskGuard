"""
Prediction Router for RiskGuard API.
Accepts infrastructure project indicators, transforms features, and runs real ML inference.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.schemas import ProjectInputSchema, PredictionResponse
from backend.services.ml_service import run_prediction_pipeline, persist_prediction
from backend.models_loader import get_precomputed_predictions_df

router = APIRouter(tags=["ML Prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_project_delay(payload: ProjectInputSchema, background_tasks: BackgroundTasks):
    """
    Run real-time machine learning inference using the production champion XGBoost model.
    Returns binary prediction, delay probability, risk score, and calibrated risk category.
    """
    data = payload.model_dump(exclude_none=True)

    # If only a project_id was passed, attempt to load its full record from database/cache
    if len(data) <= 2 and "project_id" in data and data["project_id"]:
        pid_str = str(data["project_id"])
        df_pred = get_precomputed_predictions_df()
        if not df_pred.empty:
            match = df_pred[df_pred["project_id"] == pid_str]
            if not match.empty:
                row = match.iloc[0]
                result = {
                    "project_id": pid_str,
                    "project_name": str(row.get("project_name", "Unknown")),
                    "prediction": int(row.get("target_delayed", 1 if float(row.get("delay_probability", 0.5)) >= 0.5 else 0)),
                    "delay_probability": round(float(row.get("delay_probability", 0.5)), 4),
                    "risk_score": float(row.get("risk_score", 50.0)),
                    "risk_category": str(row.get("risk_category", "MEDIUM")),
                    "top_risk_factors": [
                        str(row[f]) for f in ["top_risk_factor_1", "top_risk_factor_2", "top_risk_factor_3"]
                        if f in row and row[f] and str(row[f]) != "nan"
                    ]
                }
                return result

    try:
        result = run_prediction_pipeline(data)
        # Asynchronously persist prediction to MongoDB
        background_tasks.add_task(persist_prediction, result)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Prediction service is unavailable because model artifacts are missing.")
    except Exception:
        raise HTTPException(status_code=500, detail="Inference pipeline execution failed.")
