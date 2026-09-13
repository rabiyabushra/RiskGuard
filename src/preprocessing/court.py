"""State judicial pendency data cleaning module."""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_state

def process_court_data(raw_csv_path: str, output_dir: str) -> pd.DataFrame:
    """Clean court pendency and judicial capacity statistics."""
    os.makedirs(output_dir, exist_ok=True)
    print("Loading Court Pendency data...")
    df = pd.read_csv(raw_csv_path)

    # Standardize state key
    df["state_std"] = df["State/UT"].apply(standardize_state)

    # Exclude aggregate 'India' row from state matching
    df = df[df["State/UT"].str.lower() != "india"].copy()

    # Clean courthall shortfall string (e.g. '- 4.0' or '14.7')
    def clean_shortfall(val):
        if pd.isnull(val):
            return np.nan
        s = str(val).replace(' ', '').replace('%', '')
        try:
            return float(s)
        except ValueError:
            return np.nan

    df["courthall_shortfall_pct"] = df["Courthall shortfall (%) (2022)"].apply(clean_shortfall)
    # Median imputation for 1 missing shortfall value
    df["courthall_shortfall_pct"] = df["courthall_shortfall_pct"].fillna(df["courthall_shortfall_pct"].median())

    df["budget_per_capita_judiciary"] = pd.to_numeric(df["Budget per capita on judiciary (₹) (2020–21)"], errors='coerce')
    df["pop_per_high_court_judge"] = pd.to_numeric(df["Population per High Court Judge (2022)"], errors='coerce')
    df["pop_per_lower_court_judge"] = pd.to_numeric(df["Population per Lower Court Judge (2022)"], errors='coerce')
    df["case_clearance_rate_hc"] = pd.to_numeric(df["Case clearance rate of High Court (2022)"], errors='coerce')
    df["case_clearance_rate_lower"] = pd.to_numeric(df["Case clearance rate of Lower Court (2022)"], errors='coerce')

    # Legal Pressure Index: normalized lower court burden + courthall shortfall
    pop_norm = (df["pop_per_lower_court_judge"] - df["pop_per_lower_court_judge"].min()) / (df["pop_per_lower_court_judge"].max() - df["pop_per_lower_court_judge"].min())
    short_norm = (df["courthall_shortfall_pct"] - df["courthall_shortfall_pct"].min()) / (df["courthall_shortfall_pct"].max() - df["courthall_shortfall_pct"].min())
    df["legal_pressure_index"] = (pop_norm * 0.6) + (short_norm * 0.4)

    export_cols = [
        "state_std", "budget_per_capita_judiciary", "pop_per_high_court_judge",
        "pop_per_lower_court_judge", "courthall_shortfall_pct",
        "case_clearance_rate_hc", "case_clearance_rate_lower", "legal_pressure_index"
    ]
    df_clean = df[export_cols].drop_duplicates(subset=["state_std"])
    out_file = os.path.join(output_dir, "court_clean.csv")
    df_clean.to_csv(out_file, index=False)
    print(f"Saved cleaned Court dataset to: {out_file} ({len(df_clean)} states)")
    return df_clean

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    src = os.path.join(BASE, "data", "raw", "court", "Pendency of Court Cases in India.csv")
    dst = os.path.join(BASE, "data", "processed", "court")
    process_court_data(src, dst)
