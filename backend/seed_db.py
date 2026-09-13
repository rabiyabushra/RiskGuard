"""
MongoDB Seeding Utility for RiskGuard.
Loads processed infrastructure projects (riskguard_master.csv),
portfolio risk predictions (risk_predictions.csv), and SHAP explanations (project_explanations.json)
into MongoDB with idempotent upserts and compound indexes.
"""

import os
import sys
import json
import argparse
import pandas as pd
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))


def seed_database(mongo_uri: str = "mongodb://localhost:27017", database_name: str = "riskguard_db"):
    """
    Executes database seeding for RiskGuard.
    """
    print(f"Connecting to MongoDB at: {mongo_uri} (db: '{database_name}')...")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        print("Connected to MongoDB successfully.")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[Error] Could not connect to MongoDB server: {e}")
        print("Please ensure your MongoDB service or Docker container is running.")
        return False

    db = client[database_name]

    # 1. Ingest Master Projects & Risk Predictions
    pred_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "risk_predictions.csv")
    if not os.path.exists(pred_path):
        pred_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "riskguard_master.csv")

    if os.path.exists(pred_path):
        print(f"\nReading project dataset: {pred_path}...")
        df = pd.read_csv(pred_path)
        # Ensure project_id is string
        df["project_id"] = df["project_id"].astype(str)
        
        # Clean NaNs to None for BSON compatibility
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        print(f"Loaded {len(records)} project records.")

        project_ops = []
        prediction_ops = []

        for rec in records:
            pid = rec["project_id"]
            project_ops.append(
                UpdateOne({"project_id": pid}, {"$set": rec}, upsert=True)
            )

            # Store matching prediction record
            if "delay_probability" in rec and rec["delay_probability"] is not None:
                pred_doc = {
                    "project_id": pid,
                    "project_name": rec.get("project_name", "Unknown"),
                    "delay_probability": float(rec.get("delay_probability", 0.0)),
                    "risk_score": float(rec.get("risk_score", 0.0)),
                    "risk_category": str(rec.get("risk_category", "MEDIUM")),
                    "top_risk_factors": [
                        str(rec[f]) for f in ["top_risk_factor_1", "top_risk_factor_2", "top_risk_factor_3"]
                        if f in rec and rec[f] and str(rec[f]) != "None"
                    ],
                    "model_version": "v1.0.0-XGBoost"
                }
                prediction_ops.append(
                    UpdateOne({"project_id": pid}, {"$set": pred_doc}, upsert=True)
                )

        if project_ops:
            res_proj = db["projects"].bulk_write(project_ops)
            print(f"-> 'projects' collection updated: {res_proj.upserted_count} inserted, {res_proj.modified_count} modified.")

        if prediction_ops:
            res_pred = db["predictions"].bulk_write(prediction_ops)
            print(f"-> 'predictions' collection updated: {res_pred.upserted_count} inserted, {res_pred.modified_count} modified.")
    else:
        print(f"Warning: Project dataset not found at {pred_path}.")

    # 2. Ingest SHAP Explanations
    exp_path = os.path.join(PROJECT_ROOT, "data", "processed", "master", "project_explanations.json")
    if os.path.exists(exp_path):
        print(f"\nReading SHAP explanations: {exp_path}...")
        with open(exp_path, "r", encoding="utf-8") as f:
            exp_data = json.load(f)

        exp_ops = []
        for exp in exp_data:
            pid = str(exp["project_id"])
            exp_ops.append(
                UpdateOne({"project_id": pid}, {"$set": exp}, upsert=True)
            )

        if exp_ops:
            res_exp = db["explanations"].bulk_write(exp_ops)
            print(f"-> 'explanations' collection updated: {res_exp.upserted_count} inserted, {res_exp.modified_count} modified.")
    else:
        print(f"Warning: SHAP explanations file not found at {exp_path}.")

    # 3. Create Compound & Filter Indexes
    print("\nCreating database indexes...")
    db["projects"].create_index("project_id", unique=True)
    db["projects"].create_index("state_std")
    db["projects"].create_index("sector")
    db["projects"].create_index("risk_category")
    db["predictions"].create_index("project_id", unique=True)
    db["predictions"].create_index("risk_category")
    db["predictions"].create_index([("risk_score", -1)])
    db["explanations"].create_index("project_id", unique=True)
    print("Indexes created successfully.")

    print("\nDatabase seeding completed successfully! All collections ready for API queries.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MongoDB with RiskGuard datasets.")
    parser.add_argument("--uri", type=str, default=os.getenv("MONGO_URI", "mongodb://localhost:27017"), help="MongoDB URI")
    parser.add_argument("--db", type=str, default=os.getenv("DATABASE_NAME", "riskguard_db"), help="Database name")
    args = parser.parse_args()

    seed_database(mongo_uri=args.uri, database_name=args.db)
