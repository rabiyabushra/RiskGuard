"""Road transport statistics cleaning and consolidation module."""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_state

def process_roads_data(raw_roads_dir: str, output_dir: str) -> pd.DataFrame:
    """Consolidate road statistics from BRS 2018-19 Annexures 3.1, 7.9b, and 7.9c."""
    os.makedirs(output_dir, exist_ok=True)
    print("Loading Road Transport Annexures...")

    ann3_1 = pd.read_csv(os.path.join(raw_roads_dir, "Road_Transport_BRS_2018-19_Annexure3_1.csv"))
    ann7_9b = pd.read_csv(os.path.join(raw_roads_dir, "Road_Transport_BRS_2018-19_Annexure7_9b.csv"))
    ann7_9c = pd.read_csv(os.path.join(raw_roads_dir, "Road_Transport_BRS_2018-19_Annexure7_9c.csv"))

    # Standardize state in each
    ann3_1["state_std"] = ann3_1["Name of State / UT"].dropna().apply(standardize_state)
    ann7_9b["state_std"] = ann7_9b["Name of the States"].dropna().apply(standardize_state)
    ann7_9c["state_std"] = ann7_9c["Name of the States"].dropna().apply(standardize_state)

    # Extract 7.9b features
    cols_7_9b = {
        "Total road Length": "total_road_length",
        "National Highways": "national_highways_length",
        "State Highways": "state_highways_length",
        "District Roads": "district_roads_length",
        "Rural Roads": "rural_roads_length",
        "Road Density ": "road_density_per_1000sqkm",
        "Road Density per 1000 Sq. Km - National Highways": "nh_density_per_1000sqkm",
        "Road Density per 1000 Sq. Km - State Highways": "sh_density_per_1000sqkm"
    }
    df_b = ann7_9b[["state_std"] + list(cols_7_9b.keys())].rename(columns=cols_7_9b)

    # Extract 3.1 surfaced road features
    ann3_1["surfaced_road_length"] = pd.to_numeric(ann3_1["Surfaced"], errors='coerce')
    ann3_1["total_road_brs31"] = pd.to_numeric(ann3_1["Total "], errors='coerce')
    ann3_1["surfaced_road_ratio"] = np.where(
        ann3_1["total_road_brs31"] > 0,
        ann3_1["surfaced_road_length"] / ann3_1["total_road_brs31"],
        np.nan
    )
    df_31 = ann3_1[["state_std", "surfaced_road_length", "surfaced_road_ratio"]].dropna(subset=["state_std"])

    # Extract 7.9c population road density
    df_c = ann7_9c[["state_std", "Road length per '000 pop"]].rename(
        columns={"Road length per '000 pop": "road_length_per_1000pop"}
    )

    # Merge into unified road statistics table
    merged = df_b.merge(df_31, on="state_std", how="left").merge(df_c, on="state_std", how="left")
    df_clean = merged.drop_duplicates(subset=["state_std"])

    out_file = os.path.join(output_dir, "roads_clean.csv")
    df_clean.to_csv(out_file, index=False)
    print(f"Saved cleaned Road dataset to: {out_file} ({len(df_clean)} states)")
    return df_clean

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    src_dir = os.path.join(BASE, "data", "raw", "roads")
    dst_dir = os.path.join(BASE, "data", "processed", "roads")
    process_roads_data(src_dir, dst_dir)
