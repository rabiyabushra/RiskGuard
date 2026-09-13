"""
Unit and integration tests for RiskGuard FastAPI Backend.
Tests REST routes, real ML inference, risk analysis, SHAP attributions,
and Gemini recommendation generation (mocked & fallback).
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure RiskGuard project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.models_loader import get_precomputed_predictions_df

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_project_id():
    """Find a valid project ID from the dataset for testing."""
    df = get_precomputed_predictions_df()
    if not df.empty:
        return str(df["project_id"].iloc[0])
    return "612786"


class TestBackendAPI:
    """Complete test suite for Member 5 FastAPI backend endpoints."""

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "RiskGuard API"
        assert data["status"] == "online"
        assert "modules" in data

    def test_health_check_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert data["model_loaded"] is True
        assert data["preprocessor_loaded"] is True

    def test_list_projects(self):
        response = client.get("/projects?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "projects" in data
        assert len(data["projects"]) <= 5
        if data["total"] > 0:
            first = data["projects"][0]
            assert "project_id" in first
            assert "project_name" in first

    def test_get_single_project(self, sample_project_id):
        response = client.get(f"/projects/{sample_project_id}")
        assert response.status_code == 200
        data = response.json()
        assert str(data["project_id"]) == str(sample_project_id)
        assert "project_name" in data

    def test_get_invalid_project_returns_404(self):
        response = client.get("/projects/NON_EXISTENT_PROJECT_999999")
        assert response.status_code == 404

    def test_real_ml_prediction_endpoint(self):
        payload = {
            "project_name": "Test Greenfield Highway",
            "sector": "Road Transport & Highways",
            "state": "Gujarat",
            "original_cost": 250.0,
            "revised_cost": 280.0,
            "expenditure": 90.0,
            "physical_progress": 35.0,
            "planned_duration_days": 730
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] in (0, 1)
        assert "delay_probability" in data
        assert 0.0 <= data["delay_probability"] <= 1.0
        assert "risk_score" in data
        assert 0.0 <= data["risk_score"] <= 100.0
        assert data["risk_category"] in ("LOW", "MEDIUM", "HIGH")

    def test_risk_analysis_endpoint(self, sample_project_id):
        response = client.get(f"/risk-analysis/{sample_project_id}")
        assert response.status_code == 200
        data = response.json()
        assert str(data["project_id"]) == str(sample_project_id)
        assert "risk_score" in data
        assert "risk_category" in data
        assert "thresholds" in data
        assert data["risk_category"] in ("LOW", "MEDIUM", "HIGH")

    def test_shap_explanation_endpoint(self, sample_project_id):
        response = client.get(f"/projects/{sample_project_id}/explanation")
        assert response.status_code == 200
        data = response.json()
        assert "base_value" in data
        assert "top_risk_increasing_factors" in data
        assert "top_risk_reducing_factors" in data
        assert "narrative_explanations" in data
        assert isinstance(data["narrative_explanations"], list)

    def test_shap_global_endpoint(self):
        response = client.get("/shap/global?top_n=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
        if len(data) > 0:
            assert "feature" in data[0]
            assert "mean_abs_shap" in data[0]

    def test_recommendations_endpoint_offline_fallback(self, sample_project_id):
        # Testing recommendation generation when GEMINI_API_KEY is not configured
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            payload = {"project_id": sample_project_id}
            response = client.post("/recommendations", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data
            assert len(data["recommendations"]) > 0
            assert "risk_category" in data
            assert data["status"] in ("offline_fallback", "gemini_live", "error_fallback")

    def test_recommendations_endpoint_with_mocked_gemini(self, sample_project_id):
        # Mocking live Google Gemini API response
        mock_response = MagicMock()
        mock_response.text = (
            "- Expedite land acquisition clearance with state authorities.\n"
            "- Implement bi-weekly milestone audits to close progress gap.\n"
            "- Coordinate with state power distribution utility for priority line connection."
        )

        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model_instance

            with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_test_key"}, clear=False):
                payload = {"project_id": sample_project_id}
                response = client.post("/recommendations", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert len(data["recommendations"]) >= 3
                assert "land acquisition" in data["recommendations"][0].lower()
                assert data["model_used"] in ("gemini-flash-latest", "gemini-1.5-flash")
                assert data["status"] == "gemini_live"
