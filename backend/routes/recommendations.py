"""
Recommendations Router for RiskGuard API.
Synthesizes project details, ML delay probability, calibrated risk scores,
and top SHAP risk factors to generate actionable mitigation advice via Gemini 1.5 Flash.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException

from backend.schemas import RecommendationRequest, RecommendationResponse
from backend.services.gemini_service import generate_gemini_recommendations
from backend.services.shap_service import get_project_shap_explanation, compute_live_shap_explanation
from backend.services.risk_service import get_project_risk_by_id
from backend.services.ml_service import run_prediction_pipeline
from backend.models_loader import get_precomputed_predictions_df

router = APIRouter(tags=["AI Recommendations (Gemini)"])


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Generate actionable mitigation recommendations using Google Gemini 1.5 Flash.
    Dynamically embeds delay probability, risk score, and top SHAP risk drivers into the prompt.
    """
    proj_id = request.project_id
    custom_data = request.project_data

    # Case A: project_id provided
    if proj_id:
        pid_str = str(proj_id)
        df_pred = get_precomputed_predictions_df()
        proj_row = None
        if not df_pred.empty:
            match = df_pred[df_pred["project_id"] == pid_str]
            if not match.empty:
                proj_row = match.iloc[0].to_dict()

        shap_info = get_project_shap_explanation(pid_str)

        if not proj_row and not shap_info:
            raise HTTPException(status_code=404, detail=f"Project '{proj_id}' not found.")

        project_name = proj_row.get("project_name", shap_info.get("project_name", "Infrastructure Project")) if proj_row else shap_info.get("project_name")
        sector = proj_row.get("sector", "Infrastructure") if proj_row else "Infrastructure"
        state = proj_row.get("state_std", proj_row.get("state", "National")) if proj_row else "National"
        prob = float(proj_row.get("delay_probability", shap_info.get("delay_probability", 0.5))) if proj_row else shap_info.get("delay_probability")
        score = float(proj_row.get("risk_score", shap_info.get("risk_score", 50.0))) if proj_row else shap_info.get("risk_score")
        category = str(proj_row.get("risk_category", shap_info.get("risk_category", "MEDIUM"))) if proj_row else shap_info.get("risk_category")

        # Extract top positive drivers from SHAP info
        top_factors = []
        mitigating_factors = []
        if shap_info:
            top_factors = [item["feature"].replace("_", " ").title() for item in shap_info.get("top_risk_increasing_factors", [])[:3]]
            mitigating_factors = [item["feature"].replace("_", " ").title() for item in shap_info.get("top_risk_reducing_factors", [])[:2]]
        elif proj_row:
            top_factors = [
                str(proj_row[f]).replace("_", " ").title() for f in ["top_risk_factor_1", "top_risk_factor_2", "top_risk_factor_3"]
                if f in proj_row and proj_row[f] and str(proj_row[f]) != "nan"
            ]

    # Case B: Custom project data provided
    elif custom_data:
        pred = run_prediction_pipeline(custom_data)
        shap_info = compute_live_shap_explanation(custom_data, top_n=3)

        pid_str = str(pred["project_id"])
        project_name = pred["project_name"]
        sector = custom_data.get("sector", "Infrastructure")
        state = custom_data.get("state", "National")
        prob = pred["delay_probability"]
        score = pred["risk_score"]
        category = pred["risk_category"]

        top_factors = [item["feature"].replace("_", " ").title() for item in shap_info.get("top_risk_increasing_factors", [])[:3]]
        mitigating_factors = [item["feature"].replace("_", " ").title() for item in shap_info.get("top_risk_reducing_factors", [])[:2]]

    else:
        raise HTTPException(status_code=400, detail="Must provide either 'project_id' or 'project_data'.")

    # Generate recommendations via Gemini
    gemini_result = generate_gemini_recommendations(
        project_name=project_name,
        sector=sector,
        state=state,
        delay_probability=prob,
        risk_score=score,
        risk_category=category,
        top_risk_factors=top_factors,
        top_mitigating_factors=mitigating_factors,
        custom_context=request.custom_context
    )

    return {
        "project_id": pid_str,
        "project_name": project_name,
        "delay_probability": round(prob, 4),
        "risk_score": score,
        "risk_category": category,
        "top_risk_factors": top_factors,
        "recommendations": gemini_result["recommendations"],
        "model_used": gemini_result["model_used"],
        "status": gemini_result["status"],
        "notes": gemini_result["notes"]
    }


@router.get("/projects/{project_id}/recommendations", response_model=RecommendationResponse)
async def get_project_recommendations(project_id: str):
    """
    Convenience GET endpoint to obtain Gemini-powered recommendations for a saved project.
    """
    return await get_recommendations(RecommendationRequest(project_id=project_id))
