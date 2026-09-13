"""SHAP Explainability and Feature Attribution Engine for RiskGuard.

Initializes model-specific TreeExplainer, computes global Shapley feature importances,
extracts positive and negative risk contributors for individual projects,
synthesizes human-readable non-causal narratives, and persists explanation artifacts.
"""

import os
import json
import joblib
import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Union

from src.explainability.risk_analysis import calculate_risk_score, assign_risk_category

def get_tree_explainer(model):
    """Initialize a SHAP TreeExplainer for the champion tree/gradient boosted model."""
    return shap.TreeExplainer(model)

def compute_shap_values(explainer, X: pd.DataFrame) -> np.ndarray:
    """Compute SHAP values matrix for input features."""
    vals = explainer.shap_values(X)
    return np.array(vals)

def format_human_readable_explanation(feature_name: str, shap_val: float, raw_val: Any = None) -> str:
    """
    Generate an objective, non-causal explanation statement based on SHAP contribution.
    """
    # Clean feature name for human presentation
    clean_name = feature_name.replace("sector_", "Sector: ").replace("state_std_", "State: ")
    clean_name = clean_name.replace("_", " ").title()

    direction = "increasing" if shap_val > 0 else "decreasing"
    strength = "strongly " if abs(shap_val) > 0.2 else ""

    if shap_val > 0:
        return f"{clean_name} is {strength}contributing toward higher predicted project delay risk."
    else:
        return f"{clean_name} is {strength}contributing toward lowering the predicted delay risk."

def explain_single_project(
    project_record: Dict[str, Any],
    model,
    preprocessor,
    explainer,
    feature_names: List[str],
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Generate complete SHAP explanation breakdown for a single project record.
    """
    proj_id = str(project_record.get("project_id", "Unknown"))
    proj_name = str(project_record.get("project_name", "Unknown"))

    drop_cols = [
        "project_id", "legacy_ocms_code", "project_name", "agency", "state",
        "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
        "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
        "schedule_delay_days", "target_delayed"
    ]
    df_raw = pd.DataFrame([project_record])
    df_features = df_raw.drop(columns=[c for c in drop_cols if c in df_raw.columns], errors='ignore')

    # Transform
    X_trans = preprocessor.transform(df_features)
    X_df = pd.DataFrame(X_trans, columns=feature_names)

    # Inference
    prob = float(model.predict_proba(X_trans)[0, 1])
    score = calculate_risk_score(prob)
    category = assign_risk_category(score)

    # SHAP computation
    shap_vals = explainer.shap_values(X_df)[0]
    base_val = float(explainer.expected_value) if np.isscalar(explainer.expected_value) else float(explainer.expected_value[1] if len(explainer.expected_value) > 1 else explainer.expected_value[0])

    # Separate positive and negative contributors
    items = []
    for f, sv, val in zip(feature_names, shap_vals, X_trans[0]):
        items.append({
            "feature": f,
            "shap_value": round(float(sv), 4),
            "feature_value": round(float(val), 4)
        })

    # Sort
    positive_factors = sorted([x for x in items if x["shap_value"] > 0], key=lambda x: x["shap_value"], reverse=True)[:top_n]
    negative_factors = sorted([x for x in items if x["shap_value"] < 0], key=lambda x: x["shap_value"])[:top_n]

    # Human-readable narratives
    narratives = []
    for item in positive_factors[:3]:
        narratives.append(format_human_readable_explanation(item["feature"], item["shap_value"]))
    for item in negative_factors[:2]:
        narratives.append(format_human_readable_explanation(item["feature"], item["shap_value"]))

    return {
        "project_id": proj_id,
        "project_name": proj_name,
        "delay_probability": round(prob, 4),
        "risk_score": score,
        "risk_category": category,
        "base_value": round(base_val, 4),
        "top_risk_increasing_factors": positive_factors,
        "top_risk_reducing_factors": negative_factors,
        "narrative_explanations": narratives
    }

def run_shap_pipeline(base_dir: str):
    """Execute complete global and local SHAP explainability pipeline."""
    models_dir = os.path.join(base_dir, "models")
    master_dir = os.path.join(base_dir, "data", "processed", "master")
    reports_dir = os.path.join(base_dir, "docs", "reports", "shap")
    os.makedirs(reports_dir, exist_ok=True)

    print("=" * 60)
    print("MEMBER 4: SHAP EXPLAINABILITY & RISK ANALYSIS PIPELINE")
    print("=" * 60)

    # 1. Load artifacts
    print("Loading model, preprocessor, and datasets...")
    model = joblib.load(os.path.join(models_dir, "best_model.pkl"))
    preprocessor = joblib.load(os.path.join(models_dir, "preprocessor.pkl"))
    X_test = pd.read_csv(os.path.join(master_dir, "X_test.csv"))
    y_test = pd.read_csv(os.path.join(master_dir, "y_test.csv")).values.ravel()
    df_master = pd.read_csv(os.path.join(master_dir, "riskguard_master.csv"))

    feature_names = list(X_test.columns)
    print(f"Features: {len(feature_names)} | Test samples: {len(X_test)}")

    # 2. Initialize SHAP TreeExplainer
    print("\nInitializing SHAP TreeExplainer...")
    explainer = get_tree_explainer(model)
    shap_vals_raw = explainer.shap_values(X_test)
    base_val = explainer.expected_value
    print(f"SHAP Matrix Shape: {shap_vals_raw.shape} | Base Value: {base_val}")

    # 3. Global Feature Importance (Mean Absolute SHAP)
    mean_abs_shap = np.abs(shap_vals_raw).mean(axis=0)
    df_importance = pd.DataFrame({
        "feature": feature_names,
        "mean_abs_shap": mean_abs_shap
    }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

    global_imp_file = os.path.join(reports_dir, "global_feature_importance.csv")
    df_importance.to_csv(global_imp_file, index=False)
    print(f"Saved Global Feature Importance: {global_imp_file}")
    print("\nTop 10 Global SHAP Drivers of Delay:")
    print(df_importance.head(10).to_string(index=False))

    # 4. Generate SHAP Visualizations
    print("\nGenerating SHAP Visualizations...")

    # A. SHAP Summary (Beeswarm) Plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_vals_raw, X_test, show=False, max_display=15)
    plt.title("SHAP Summary Plot: Top 15 Feature Impacts on Delay Prediction", fontsize=12)
    plt.tight_layout()
    summary_path = os.path.join(reports_dir, "shap_summary.png")
    plt.savefig(summary_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {summary_path}")

    # B. SHAP Feature Importance Bar Chart
    plt.figure(figsize=(9, 6))
    top15 = df_importance.head(15)
    sns.barplot(data=top15, x="mean_abs_shap", y="feature", palette="rocket")
    plt.title("SHAP Feature Importance (Mean |SHAP Value| Across Test Set)")
    plt.xlabel("Mean |SHAP Value|")
    plt.ylabel("Feature")
    plt.tight_layout()
    bar_path = os.path.join(reports_dir, "shap_feature_importance.png")
    plt.savefig(bar_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {bar_path}")

    # C. Model Native Feature Importance (Gain)
    plt.figure(figsize=(9, 6))
    native_importances = model.feature_importances_
    top_indices = np.argsort(native_importances)[::-1][:15]
    top_native_df = pd.DataFrame({
        "feature": [feature_names[i] for i in top_indices],
        "native_gain": native_importances[top_indices]
    })
    sns.barplot(data=top_native_df, x="native_gain", y="feature", palette="mako")
    plt.title("Model Native Feature Importance (XGBoost Gain)")
    plt.xlabel("Relative Gain Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    native_path = os.path.join(reports_dir, "model_feature_importance.png")
    plt.savefig(native_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {native_path}")

    # 5. Risk Category Distribution across Entire Master Portfolio
    print("\nGenerating Risk Scores and Categories across all projects...")
    drop_cols = [
        "project_id", "legacy_ocms_code", "project_name", "agency", "state",
        "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
        "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
        "schedule_delay_days", "target_delayed"
    ]
    df_features_master = df_master.drop(columns=[c for c in drop_cols if c in df_master.columns], errors='ignore')
    X_master_trans = preprocessor.transform(df_features_master)
    master_probs = model.predict_proba(X_master_trans)[:, 1]

    df_master["delay_probability"] = np.round(master_probs, 4)
    df_master["risk_score"] = df_master["delay_probability"].apply(calculate_risk_score)
    df_master["risk_category"] = df_master["risk_score"].apply(assign_risk_category)

    # Top risk factors for each project
    shap_master_sample = explainer.shap_values(pd.DataFrame(X_master_trans, columns=feature_names))
    top_factors_col1 = []
    top_factors_col2 = []
    top_factors_col3 = []
    for row_shap in shap_master_sample:
        sorted_f_idx = np.argsort(row_shap)[::-1]
        top_factors_col1.append(feature_names[sorted_f_idx[0]])
        top_factors_col2.append(feature_names[sorted_f_idx[1]])
        top_factors_col3.append(feature_names[sorted_f_idx[2]])

    df_master["top_risk_factor_1"] = top_factors_col1
    df_master["top_risk_factor_2"] = top_factors_col2
    df_master["top_risk_factor_3"] = top_factors_col3

    # Export data/processed/master/risk_predictions.csv
    risk_pred_file = os.path.join(master_dir, "risk_predictions.csv")
    df_master.to_csv(risk_pred_file, index=False)
    print(f"Saved Master Risk Predictions: {risk_pred_file} ({len(df_master)} projects)")

    # Risk Distribution Table
    cat_counts = df_master["risk_category"].value_counts()
    cat_pcts = df_master["risk_category"].value_counts(normalize=True) * 100
    df_dist = pd.DataFrame({
        "Risk Category": cat_counts.index,
        "Project Count": cat_counts.values,
        "Percentage (%)": np.round(cat_pcts.values, 2)
    })
    dist_file = os.path.join(reports_dir, "risk_distribution.csv")
    df_dist.to_csv(dist_file, index=False)
    print(f"Saved Risk Distribution: {dist_file}")
    print("\nPortfolio Risk Breakdown:")
    print(df_dist.to_string(index=False))

    # D. Risk Category Distribution Chart
    plt.figure(figsize=(7, 5))
    colors = {"LOW": "#2ecc71", "MEDIUM": "#f39c12", "HIGH": "#e74c3c"}
    sns.barplot(data=df_dist, x="Risk Category", y="Project Count", palette=colors)
    for idx, row in df_dist.iterrows():
        plt.text(idx, row["Project Count"] + 20, f"{row['Project Count']} ({row['Percentage (%)']}%)", ha="center", fontweight="bold")
    plt.title("Portfolio Risk Category Distribution (N=1,941 Projects)")
    plt.ylabel("Number of Infrastructure Projects")
    plt.ylim(0, df_dist["Project Count"].max() * 1.15)
    plt.tight_layout()
    dist_chart_path = os.path.join(reports_dir, "risk_category_distribution.png")
    plt.savefig(dist_chart_path, dpi=200)
    plt.close()
    print(f"Saved: {dist_chart_path}")

    # 6. Individual Project Explanation Visualization & JSON export
    print("\nGenerating Representative Individual Project Explanation...")
    # Select high-risk project
    high_risk_sample = df_master[df_master["risk_category"] == "HIGH"].iloc[0].to_dict()
    explanation_high = explain_single_project(high_risk_sample, model, preprocessor, explainer, feature_names)

    # Plot Individual Project Explanation Bar Chart
    plt.figure(figsize=(9, 5))
    pos_df = pd.DataFrame(explanation_high["top_risk_increasing_factors"])
    neg_df = pd.DataFrame(explanation_high["top_risk_reducing_factors"])
    combo = pd.concat([pos_df, neg_df]).sort_values(by="shap_value")

    bar_colors = ["#e74c3c" if sv > 0 else "#2ecc71" for sv in combo["shap_value"]]
    plt.barh(combo["feature"], combo["shap_value"], color=bar_colors)
    plt.axvline(0, color="gray", linestyle="--", alpha=0.7)
    plt.title(f"SHAP Local Attribution: Project {explanation_high['project_id']}\n(Score: {explanation_high['risk_score']} | Category: {explanation_high['risk_category']})")
    plt.xlabel("SHAP Value (Contribution toward Delay Prediction)")
    plt.tight_layout()
    indiv_path = os.path.join(reports_dir, "individual_project_explanation.png")
    plt.savefig(indiv_path, dpi=200)
    plt.close()
    print(f"Saved: {indiv_path}")

    # 7. Generate data/processed/master/project_explanations.json
    print("\nGenerating individual explanations JSON for representative test set...")
    explanations_list = []
    sample_projects = df_master.head(50).to_dict(orient="records")
    for proj in sample_projects:
        exp = explain_single_project(proj, model, preprocessor, explainer, feature_names)
        explanations_list.append(exp)

    json_path = os.path.join(master_dir, "project_explanations.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(explanations_list, f, indent=2)
    print(f"Saved Project Explanations JSON: {json_path} ({len(explanations_list)} detailed project profiles)")

    print("=" * 60)
    print("MEMBER 4 SHAP PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    run_shap_pipeline(BASE)
