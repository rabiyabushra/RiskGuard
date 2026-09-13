"""
Unit tests for Risk Analysis and SHAP Explainability modules.
Tests risk scoring, category thresholds, project risk generation, and SHAP pipeline functions.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
import joblib

# Ensure RiskGuard root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.explainability.risk_analysis import (
    calculate_risk_score,
    assign_risk_category,
    generate_project_risk,
    batch_calculate_risk
)
from src.explainability.shap_analysis import (
    get_tree_explainer,
    compute_shap_values,
    format_human_readable_explanation,
    explain_single_project
)


class TestRiskScoring:
    """Test suite for probability-to-risk-score transformations and categorization."""

    def test_risk_score_calculation_standards(self):
        assert calculate_risk_score(0.0) == 0.0
        assert calculate_risk_score(0.5) == 50.0
        assert calculate_risk_score(0.852) == 85.2
        assert calculate_risk_score(1.0) == 100.0

    def test_risk_score_clamping(self):
        # Clamping negative probabilities
        assert calculate_risk_score(-0.25) == 0.0
        # Clamping probabilities greater than 1
        assert calculate_risk_score(1.5) == 100.0

    def test_risk_category_assignment_boundaries(self):
        # LOW: score < 35
        assert assign_risk_category(0.0) == "LOW"
        assert assign_risk_category(20.5) == "LOW"
        assert assign_risk_category(34.99) == "LOW"

        # MEDIUM: 35 <= score < 65
        assert assign_risk_category(35.0) == "MEDIUM"
        assert assign_risk_category(50.0) == "MEDIUM"
        assert assign_risk_category(64.99) == "MEDIUM"

        # HIGH: score >= 65
        assert assign_risk_category(65.0) == "HIGH"
        assert assign_risk_category(85.0) == "HIGH"
        assert assign_risk_category(100.0) == "HIGH"

    def test_batch_calculate_risk(self):
        df = pd.DataFrame({
            "project_id": [1, 2, 3],
            "cost": [100, 200, 300]
        })
        probs = [0.10, 0.45, 0.90]
        enriched = batch_calculate_risk(df, probs)

        assert "delay_probability" in enriched.columns
        assert "risk_score" in enriched.columns
        assert "risk_category" in enriched.columns

        assert enriched["risk_category"].tolist() == ["LOW", "MEDIUM", "HIGH"]
        assert enriched["risk_score"].tolist() == [10.0, 45.0, 90.0]

    def test_generate_project_risk(self, model_and_data):
        df_master = model_and_data["df_master"]
        record = df_master.iloc[0].to_dict()

        res = generate_project_risk(record)
        assert "prediction" in res
        assert "delay_probability" in res
        assert "risk_score" in res
        assert "risk_category" in res
        assert res["prediction"] in (0, 1)
        assert 0.0 <= res["delay_probability"] <= 1.0
        assert 0.0 <= res["risk_score"] <= 100.0
        assert res["risk_category"] in ("LOW", "MEDIUM", "HIGH")


@pytest.fixture(scope="module")
def model_and_data():
    model_path = os.path.join(PROJECT_ROOT, "models", "best_model.pkl")
    preprocessor_path = os.path.join(PROJECT_ROOT, "models", "preprocessor.pkl")
    x_test_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "X_test.csv")
    master_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "riskguard_master.csv")

    if not os.path.exists(model_path) or not os.path.exists(x_test_path):
        pytest.skip("Model or test data not found.")

    model = joblib.load(model_path)
    preprocessor = joblib.load(preprocessor_path) if os.path.exists(preprocessor_path) else None
    X_test = pd.read_csv(x_test_path)
    df_master = pd.read_csv(master_path) if os.path.exists(master_path) else None

    return {
        "model": model,
        "preprocessor": preprocessor,
        "X_test": X_test,
        "df_master": df_master
    }


class TestSHAPExplainability:
    """Test suite for SHAP explanations and TreeExplainer integration."""

    def test_tree_explainer_initialization(self, model_and_data):
        model = model_and_data["model"]
        explainer = get_tree_explainer(model)
        assert explainer is not None

        # Check expected value exists
        ev = explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            ev_val = float(ev[1] if len(ev) > 1 else ev[0])
        else:
            ev_val = float(ev)
        assert -10.0 <= ev_val <= 10.0

    def test_shap_values_computation_and_shape(self, model_and_data):
        model = model_and_data["model"]
        X_test = model_and_data["X_test"].iloc[:10]  # First 10 samples
        explainer = get_tree_explainer(model)

        shap_vals = compute_shap_values(explainer, X_test)
        assert isinstance(shap_vals, np.ndarray)
        assert shap_vals.shape == (10, X_test.shape[1])
        assert not np.isnan(shap_vals).any()

    def test_shap_local_additivity(self, model_and_data):
        """Verify that base_value + sum(shap_values) equals model raw prediction margin."""
        model = model_and_data["model"]
        sample = model_and_data["X_test"].iloc[[0]]
        explainer = get_tree_explainer(model)

        shap_vals = compute_shap_values(explainer, sample)
        shap_val = shap_vals[0]
        ev = explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            base_val = float(ev[1] if len(ev) > 1 else ev[0])
        else:
            base_val = float(ev)

        reconstructed_margin = base_val + float(np.sum(shap_val))
        raw_margin = float(model.predict(sample, output_margin=True)[0])
        assert np.isclose(reconstructed_margin, raw_margin, atol=1e-3)

    def test_human_readable_explanation_formatting(self):
        desc_pos = format_human_readable_explanation("physical_progress", 0.85, 25.0)
        assert "physical progress" in desc_pos.lower()
        assert "contributing toward" in desc_pos.lower()
        assert "delay risk" in desc_pos.lower()

        desc_neg = format_human_readable_explanation("expenditure_ratio", -0.45, 0.90)
        assert "expenditure ratio" in desc_neg.lower()
        assert "lowering" in desc_neg.lower()
        assert "delay risk" in desc_neg.lower()

    def test_single_project_explanation_structure(self, model_and_data):
        model = model_and_data["model"]
        preprocessor = model_and_data["preprocessor"]
        df_master = model_and_data["df_master"]
        explainer = get_tree_explainer(model)
        feature_names = model_and_data["X_test"].columns.tolist()

        record = df_master.iloc[0].to_dict()

        explanation = explain_single_project(
            project_record=record,
            model=model,
            preprocessor=preprocessor,
            explainer=explainer,
            feature_names=feature_names,
            top_n=5
        )

        assert "project_id" in explanation
        assert "project_name" in explanation
        assert "delay_probability" in explanation
        assert "risk_score" in explanation
        assert "risk_category" in explanation
        assert "base_value" in explanation
        assert "top_risk_increasing_factors" in explanation
        assert "top_risk_reducing_factors" in explanation
        assert "narrative_explanations" in explanation

        assert len(explanation["top_risk_increasing_factors"]) <= 5
        assert len(explanation["top_risk_reducing_factors"]) <= 5
        assert isinstance(explanation["narrative_explanations"], list)
