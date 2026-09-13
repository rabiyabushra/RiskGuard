"""Train/test preparation and preprocessing pipeline module for Member 3.

Separates features and targets, enforces strict zero target-leakage rules,
encodes categorical variables using a pipeline fitted strictly on training data,
and produces stratified train/test sets.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

def prepare_train_test_data(master_csv_path: str, output_dir: str, models_dir: str):
    """Split master dataset into train and test splits with fitted preprocessor."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    print("Loading Master Dataset for Train/Test preparation...")
    df = pd.read_csv(master_csv_path)

    # 1. Target separation
    y = df["target_delayed"].copy()

    # 2. Strict anti-leakage feature drop:
    # Exclude IDs, text names, raw timestamps, and direct target mathematical derivatives (schedule_delay_days)
    drop_cols = [
        "project_id", "legacy_ocms_code", "project_name", "agency", "state",
        "date_of_approval", "start_date", "original_completion_date", "revised_completion_date",
        "date_of_approval_dt", "start_date_dt", "original_completion_date_dt", "revised_completion_date_dt",
        "schedule_delay_days", "target_delayed"
    ]
    X_raw = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Categorical and numerical columns
    categorical_cols = ["sector", "state_std"]
    numerical_cols = [c for c in X_raw.columns if c not in categorical_cols and pd.api.types.is_numeric_dtype(X_raw[c])]

    print(f"Features selected: {len(numerical_cols)} numerical, {len(categorical_cols)} categorical.")

    # 3. Stratified Train/Test split (80% train, 20% test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train size: {len(X_train_raw)} | Test size: {len(X_test_raw)}")

    # 4. Construct Scikit-Learn Preprocessing Pipeline
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, numerical_cols),
            ("cat", cat_pipeline, categorical_cols)
        ]
    )

    # Fit ONLY on training data to prevent data leakage!
    print("Fitting preprocessor strictly on X_train...")
    X_train_trans = preprocessor.fit_transform(X_train_raw)
    X_test_trans = preprocessor.transform(X_test_raw)

    # Reconstruct feature column names
    encoded_cat_names = preprocessor.named_transformers_["cat"].named_steps["onehot"].get_feature_names_out(categorical_cols)
    final_feature_names = numerical_cols + list(encoded_cat_names)

    X_train_df = pd.DataFrame(X_train_trans, columns=final_feature_names, index=X_train_raw.index)
    X_test_df = pd.DataFrame(X_test_trans, columns=final_feature_names, index=X_test_raw.index)

    # 5. Export splits
    X_train_df.to_csv(os.path.join(output_dir, "X_train.csv"), index=False)
    X_test_df.to_csv(os.path.join(output_dir, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(output_dir, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(output_dir, "y_test.csv"), index=False)

    # Save preprocessing artifact
    pipeline_file = os.path.join(models_dir, "preprocessor.joblib")
    joblib.dump(preprocessor, pipeline_file)

    print("=" * 60)
    print("TRAIN/TEST SPLIT EXPORT COMPLETE")
    print(f"X_train: {X_train_df.shape} | X_test: {X_test_df.shape}")
    print(f"y_train: {y_train.shape} (Delayed: {y_train.sum()}, Non-delayed: {len(y_train) - y_train.sum()})")
    print(f"y_test:  {y_test.shape} (Delayed: {y_test.sum()}, Non-delayed: {len(y_test) - y_test.sum()})")
    print(f"Saved fitted preprocessor to: {pipeline_file}")
    print("=" * 60)

if __name__ == "__main__":
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    master_csv = os.path.join(BASE, "data", "processed", "master", "riskguard_master.csv")
    out_master = os.path.join(BASE, "data", "processed", "master")
    models_dir = os.path.join(BASE, "models")
    prepare_train_test_data(master_csv, out_master, models_dir)
