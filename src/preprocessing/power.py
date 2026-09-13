"""Power infrastructure data cleaning and power gap calculation module."""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_state

def process_power_data(raw_csv_path: str, output_dir: str) -> pd.DataFrame:
    """Clean power infrastructure data, select latest fiscal year, and derive power gap."""
    os.makedirs(output_dir, exist_ok=True)
    print("Loading Power Infrastructure data...")
    df = pd.read_csv(raw_csv_path)

    # Standardize state
    df["state_std"] = df["State/Union Territory"].apply(standardize_state)

    # Replace '-' string placeholders with NaN
    numeric_cols = [
        "Power_Requirement_Net_Crore_Units",
        "Availability_Of_Power_Net_Crore_Units",
        "Availability_Of_Power_Per_Capita_kiloWatt-Hour",
        "Installed_Power_Capacity_MegaWatt"
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c].replace('-', np.nan), errors='coerce')

    # Benchmark year selection: 2020-21 (latest comprehensive fiscal year)
    df_2021 = df[df["Year"] == "2020-21"].copy()

    # If state has missing 2020-21, fallback to most recent valid year per state
    df_sorted = df.sort_values(by=["state_std", "Year"])
    df_latest = df_sorted.groupby("state_std").last().reset_index()

    # Derived power metrics
    df_latest["power_requirement"] = df_latest["Power_Requirement_Net_Crore_Units"]
    df_latest["power_availability"] = df_latest["Availability_Of_Power_Net_Crore_Units"]
    df_latest["power_gap"] = df_latest["power_requirement"] - df_latest["power_availability"]
    df_latest["power_gap_percent"] = np.where(
        df_latest["power_requirement"] > 0,
        (df_latest["power_gap"] / df_latest["power_requirement"]) * 100,
        0
    )
    df_latest["installed_power_capacity"] = df_latest["Installed_Power_Capacity_MegaWatt"]
    df_latest["power_per_capita"] = df_latest["Availability_Of_Power_Per_Capita_kiloWatt-Hour"]

    export_cols = [
        "state_std", "power_requirement", "power_availability",
        "power_gap", "power_gap_percent", "installed_power_capacity", "power_per_capita"
    ]
    df_clean = df_latest[export_cols].drop_duplicates(subset=["state_std"])
    out_file = os.path.join(output_dir, "power_clean.csv")
    df_clean.to_csv(out_file, index=False)
    print(f"Saved cleaned Power dataset to: {out_file} ({len(df_clean)} states)")
    return df_clean

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    src = os.path.join(BASE, "data", "raw", "power", "India_Statewise_Power_Infrastructure_Data_RBI.csv")
    dst = os.path.join(BASE, "data", "processed", "power")
    process_power_data(src, dst)
