"""Gujarat private property/RERA project cleaning and aggregation module."""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_district

def process_private_property_data(raw_csv_path: str, output_dir: str) -> pd.DataFrame:
    """Clean Gujarat RERA project data and aggregate into district-level pressure metrics."""
    os.makedirs(output_dir, exist_ok=True)
    print("Loading Gujarat RERA project data...")
    df = pd.read_csv(raw_csv_path, low_memory=False)

    df["state_std"] = "Gujarat"
    df["district_std"] = df["distName"].apply(standardize_district)

    # Clean numeric fields
    df["totalEstimatedCost"] = pd.to_numeric(df["totalEstimatedCost"], errors='coerce')
    df["totalUnits"] = pd.to_numeric(df["totalUnits"], errors='coerce')
    df["avgCostPerSqFt"] = pd.to_numeric(df["avgCostPerSqFt"], errors='coerce')

    # Aggregate to district level in Gujarat
    district_agg = df.groupby(["state_std", "district_std"]).agg(
        private_project_count=("projectRegId", "count"),
        private_project_cost_total=("totalEstimatedCost", "sum"),
        private_project_cost_mean=("totalEstimatedCost", "mean"),
        private_project_units_total=("totalUnits", "sum"),
        private_avg_cost_per_sqft=("avgCostPerSqFt", "median")
    ).reset_index()

    # Convert total cost to Rs. Crore for scale consistency with PAIMANA
    district_agg["private_project_cost_total_cr"] = district_agg["private_project_cost_total"] / 1e7
    district_agg["private_project_cost_mean_cr"] = district_agg["private_project_cost_mean"] / 1e7

    out_file = os.path.join(output_dir, "private_property_clean.csv")
    district_agg.to_csv(out_file, index=False)
    print(f"Saved cleaned Gujarat Private Property aggregations to: {out_file} ({len(district_agg)} districts)")
    return district_agg

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    src = os.path.join(BASE, "data", "raw", "private_property", "ProjectInfo_Gujarat.csv")
    dst = os.path.join(BASE, "data", "processed", "private_property")
    process_private_property_data(src, dst)
