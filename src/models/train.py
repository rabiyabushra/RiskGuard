"""Model training, hyperparameter tuning, and model persistence pipeline.

Trains Logistic Regression, Random Forest, and XGBoost classifiers on
processed PAIMANA infrastructure project data. Tunes hyper-parameters using
cross-validation strictly on the training partition, evaluates on the untouched
test partition, selects the champion model by ROC-AUC, and persists artifacts.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)

def train_and_evaluate_models(base_dir: str):
    """Execute complete training, tuning, evaluation, and selection pipeline."""
    master_dir = os.path.join(base_dir, "data", "processed", "master")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print("=" * 60)
    print("MEMBER 3: MODEL TRAINING & SELECTION PIPELINE")
    print("=" * 60)

    # 1. Load Train and Test Data
    print("Loading prepared train/test splits...")
    X_train = pd.read_csv(os.path.join(master_dir, "X_train.csv"))
    X_test = pd.read_csv(os.path.join(master_dir, "X_test.csv"))
    y_train = pd.read_csv(os.path.join(master_dir, "y_train.csv")).values.ravel()
    y_test = pd.read_csv(os.path.join(master_dir, "y_test.csv")).values.ravel()

    print(f"X_train: {X_train.shape} | X_test: {X_test.shape}")
    print(f"y_train: {len(y_train)} (Positive: {y_train.sum()})")
    print(f"y_test:  {len(y_test)} (Positive: {y_test.sum()})")

    # 2. Model 1: Logistic Regression Baseline
    print("\n[1/3] Training Logistic Regression Baseline...")
    lr = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs')
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_prob = lr.predict_proba(X_test)[:, 1]

    lr_metrics = {
        "accuracy": float(accuracy_score(y_test, lr_pred)),
        "precision": float(precision_score(y_test, lr_pred, zero_division=0)),
        "recall": float(recall_score(y_test, lr_pred)),
        "f1": float(f1_score(y_test, lr_pred)),
        "roc_auc": float(roc_auc_score(y_test, lr_prob))
    }
    print(f"Logistic Regression: ROC-AUC = {lr_metrics['roc_auc']:.4f} | F1 = {lr_metrics['f1']:.4f} | Acc = {lr_metrics['accuracy']:.4f}")
    joblib.dump(lr, os.path.join(models_dir, "logistic_regression.pkl"))

    # 3. Model 2: Random Forest Classifier + Tuning
    print("\n[2/3] Tuning and Training Random Forest...")
    rf_params = {
        "n_estimators": [100, 200],
        "max_depth": [6, 10, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2]
    }
    rf_base = RandomForestClassifier(random_state=42, n_jobs=-1)
    rf_grid = GridSearchCV(rf_base, rf_params, cv=5, scoring='roc_auc', n_jobs=-1)
    rf_grid.fit(X_train, y_train)

    best_rf = rf_grid.best_estimator_
    print(f"Best RF Parameters: {rf_grid.best_params_}")
    rf_pred = best_rf.predict(X_test)
    rf_prob = best_rf.predict_proba(X_test)[:, 1]

    rf_metrics = {
        "accuracy": float(accuracy_score(y_test, rf_pred)),
        "precision": float(precision_score(y_test, rf_pred, zero_division=0)),
        "recall": float(recall_score(y_test, rf_pred)),
        "f1": float(f1_score(y_test, rf_pred)),
        "roc_auc": float(roc_auc_score(y_test, rf_prob)),
        "best_params": rf_grid.best_params_
    }
    print(f"Random Forest: ROC-AUC = {rf_metrics['roc_auc']:.4f} | F1 = {rf_metrics['f1']:.4f} | Acc = {rf_metrics['accuracy']:.4f}")
    joblib.dump(best_rf, os.path.join(models_dir, "random_forest.pkl"))

    # 4. Model 3: XGBoost Classifier + Tuning
    print("\n[3/3] Tuning and Training XGBoost...")
    xgb_params = {
        "n_estimators": [100, 200],
        "max_depth": [3, 5],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0]
    }
    xgb_base = XGBClassifier(random_state=42, eval_metric='logloss', n_jobs=-1)
    xgb_grid = GridSearchCV(xgb_base, xgb_params, cv=5, scoring='roc_auc', n_jobs=-1)
    xgb_grid.fit(X_train, y_train)

    best_xgb = xgb_grid.best_estimator_
    print(f"Best XGBoost Parameters: {xgb_grid.best_params_}")
    xgb_pred = best_xgb.predict(X_test)
    xgb_prob = best_xgb.predict_proba(X_test)[:, 1]

    xgb_metrics = {
        "accuracy": float(accuracy_score(y_test, xgb_pred)),
        "precision": float(precision_score(y_test, xgb_pred, zero_division=0)),
        "recall": float(recall_score(y_test, xgb_pred)),
        "f1": float(f1_score(y_test, xgb_pred)),
        "roc_auc": float(roc_auc_score(y_test, xgb_prob)),
        "best_params": xgb_grid.best_params_
    }
    print(f"XGBoost: ROC-AUC = {xgb_metrics['roc_auc']:.4f} | F1 = {xgb_metrics['f1']:.4f} | Acc = {xgb_metrics['accuracy']:.4f}")
    joblib.dump(best_xgb, os.path.join(models_dir, "xgboost.pkl"))

    # Also save preprocessor.pkl copy if preprocessor.joblib exists
    prep_src = os.path.join(models_dir, "preprocessor.joblib")
    prep_dst = os.path.join(models_dir, "preprocessor.pkl")
    if os.path.exists(prep_src) and not os.path.exists(prep_dst):
        prep = joblib.load(prep_src)
        joblib.dump(prep, prep_dst)
        print(f"Saved preprocessor to {prep_dst}")

    # 5. Model Selection (Primary criterion: ROC-AUC)
    models = {
        "Logistic Regression": (lr, lr_metrics),
        "Random Forest": (best_rf, rf_metrics),
        "XGBoost": (best_xgb, xgb_metrics)
    }

    # Sort by ROC-AUC descending
    ranked = sorted(models.items(), key=lambda x: x[1][1]["roc_auc"], reverse=True)
    best_name, (best_model_obj, best_m) = ranked[0]
    print(f"\n>>> CHAMPION MODEL SELECTED: {best_name} (ROC-AUC: {best_m['roc_auc']:.4f})")

    joblib.dump(best_model_obj, os.path.join(models_dir, "best_model.pkl"))

    # 6. Save Metadata
    metadata = {
        "project": "RiskGuard",
        "champion_model": best_name,
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_name": "target_delayed",
        "target_definition": "1 if schedule_delay_days > 0 else 0",
        "train_size": len(X_train),
        "test_size": len(X_test),
        "feature_count": len(X_train.columns),
        "feature_names": list(X_train.columns),
        "random_state": 42,
        "model_performance": {
            "Logistic Regression": lr_metrics,
            "Random Forest": rf_metrics,
            "XGBoost": xgb_metrics
        }
    }
    metadata_file = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to {metadata_file}")

    print("=" * 60)
    print("MODEL TRAINING COMPLETE")
    print("=" * 60)
    return metadata

if __name__ == "__main__":
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    train_and_evaluate_models(BASE)
