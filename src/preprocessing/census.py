"""Census 2011 demographic data cleaning and aggregation module."""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_state, standardize_district

def process_census_data(raw_excel_path: str, output_dir: str) -> pd.DataFrame:
    """Load Census 2011, filter State-level summaries, and calculate demographic features."""
    os.makedirs(output_dir, exist_ok=True)
    print("Loading Census Excel sheet 'Data'...")
    df_raw = pd.read_excel(raw_excel_path, sheet_name="Data")

    # Isolate State level with TRU == 'Total'
    df_state = df_raw[(df_raw["Level"] == "STATE") & (df_raw["TRU"] == "Total")].copy()

    # Standardize state name
    df_state["state_std"] = df_state["Name"].apply(standardize_state)

    # Derived demographic indicators
    df_state["population"] = df_state["TOT_P"]
    df_state["households"] = df_state["No_HH"]
    df_state["male_population"] = df_state["TOT_M"]
    df_state["female_population"] = df_state["TOT_F"]
    df_state["female_population_ratio"] = df_state["TOT_F"] / df_state["TOT_P"]
    df_state["literacy_rate"] = (df_state["P_LIT"] / df_state["TOT_P"]) * 100
    df_state["worker_rate"] = (df_state["TOT_WORK_P"] / df_state["TOT_P"]) * 100
    df_state["non_worker_rate"] = (df_state["NON_WORK_P"] / df_state["TOT_P"]) * 100
    df_state["avg_household_size"] = df_state["TOT_P"] / np.where(df_state["No_HH"] > 0, df_state["No_HH"], np.nan)

    export_cols = [
        "state_std", "population", "households", "male_population",
        "female_population", "female_population_ratio", "literacy_rate",
        "worker_rate", "non_worker_rate", "avg_household_size"
    ]
    df_clean = df_state[export_cols].drop_duplicates(subset=["state_std"])
    out_file = os.path.join(output_dir, "census_clean.csv")
    df_clean.to_csv(out_file, index=False)
    print(f"Saved cleaned Census dataset to: {out_file} ({len(df_clean)} states)")
    return df_clean

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    src = os.path.join(BASE, "data", "raw", "census", "2011-IndiaStateDistSbDistTwn-0000.xlsx")
    dst = os.path.join(BASE, "data", "processed", "census")
    process_census_data(src, dst)
