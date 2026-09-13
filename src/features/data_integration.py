"""Data integration pipeline for RiskGuard.

Strictly maintains ONE ROW = ONE PAIMANA INFRASTRUCTURE PROJECT (1,941 rows).
Left-joins State Census demographics, Court pendency metrics, Power infrastructure,
Road connectivity, and Gujarat district private property context.
"""

import os
import pandas as pd
import numpy as np
from src.preprocessing.geo_standards import standardize_state, standardize_district
from src.features.feature_engineering import build_project_features

def integrate_datasets(base_dir: str) -> pd.DataFrame:
    """Perform verified left-joins across all processed domain tables."""
    processed_dir = os.path.join(base_dir, "data", "processed")

    # 1. Primary Backbone: PAIMANA projects
    paimana_file = os.path.join(processed_dir, "paimana", "paimana_clean.csv")
    print(f"Loading primary backbone: {paimana_file}")
    df_paimana = pd.read_csv(paimana_file)
    n_initial = len(df_paimana)
    print(f"Primary project count: {n_initial}")

    # Standardize state key on PAIMANA
    df_paimana["state_std"] = df_paimana["state"].apply(standardize_state)
    df_paimana = build_project_features(df_paimana)

    # 2. Secondary: Census Demographics (State level)
    census_file = os.path.join(processed_dir, "census", "census_clean.csv")
    df_census = pd.read_csv(census_file)
    print(f"Merging Census data ({len(df_census)} states)...")
    df_master = df_paimana.merge(df_census, on="state_std", how="left")
    assert len(df_master) == n_initial, f"Row count changed after Census merge! {len(df_master)} vs {n_initial}"

    # 3. Secondary: Court Pendency (State level)
    court_file = os.path.join(processed_dir, "court", "court_clean.csv")
    df_court = pd.read_csv(court_file)
    print(f"Merging Court Pendency data ({len(df_court)} states)...")
    df_master = df_master.merge(df_court, on="state_std", how="left")
    assert len(df_master) == n_initial, f"Row count changed after Court merge! {len(df_master)} vs {n_initial}"

    # 4. Secondary: Power Infrastructure (State level)
    power_file = os.path.join(processed_dir, "power", "power_clean.csv")
    df_power = pd.read_csv(power_file)
    print(f"Merging Power data ({len(df_power)} states)...")
    df_master = df_master.merge(df_power, on="state_std", how="left")
    assert len(df_master) == n_initial, f"Row count changed after Power merge! {len(df_master)} vs {n_initial}"

    # 5. Secondary: Road Connectivity (State level)
    roads_file = os.path.join(processed_dir, "roads", "roads_clean.csv")
    df_roads = pd.read_csv(roads_file)
    print(f"Merging Road connectivity data ({len(df_roads)} states)...")
    df_master = df_master.merge(df_roads, on="state_std", how="left")
    assert len(df_master) == n_initial, f"Row count changed after Roads merge! {len(df_master)} vs {n_initial}"

    # 6. Secondary: Gujarat Private Property context
    # Attach state-level or district-level private real-estate summary for Gujarat projects only
    private_file = os.path.join(processed_dir, "private_property", "private_property_clean.csv")
    df_private = pd.read_csv(private_file)
    
    # State-level Gujarat totals for projects sited in Gujarat
    guj_state_summary = {
        "state_std": "Gujarat",
        "gujarat_private_project_count": df_private["private_project_count"].sum(),
        "gujarat_private_total_cost_cr": df_private["private_project_cost_total_cr"].sum(),
        "gujarat_private_avg_cost_sqft": df_private["private_avg_cost_per_sqft"].median()
    }
    df_guj = pd.DataFrame([guj_state_summary])
    
    print("Attaching Gujarat Private Property context...")
    df_master = df_master.merge(df_guj, on="state_std", how="left")
    assert len(df_master) == n_initial, f"Row count changed after Private Property merge! {len(df_master)} vs {n_initial}"

    # Fill private property columns for non-Gujarat states with 0 (since non-applicable)
    df_master["gujarat_private_project_count"] = df_master["gujarat_private_project_count"].fillna(0)
    df_master["gujarat_private_total_cost_cr"] = df_master["gujarat_private_total_cost_cr"].fillna(0)
    df_master["gujarat_private_avg_cost_sqft"] = df_master["gujarat_private_avg_cost_sqft"].fillna(0)

    # Impute missing state-level features for Multi-States or small UTs using national median
    feature_impute_cols = [
        "population", "households", "literacy_rate", "worker_rate",
        "budget_per_capita_judiciary", "pop_per_lower_court_judge", "courthall_shortfall_pct",
        "legal_pressure_index", "power_requirement", "power_gap", "installed_power_capacity",
        "road_density_per_1000sqkm", "surfaced_road_ratio"
    ]
    for c in feature_impute_cols:
        if c in df_master.columns:
            median_val = df_master[c].median()
            df_master[c] = df_master[c].fillna(median_val)

    # Export master dataset
    master_dir = os.path.join(processed_dir, "master")
    os.makedirs(master_dir, exist_ok=True)
    master_file = os.path.join(master_dir, "riskguard_master.csv")
    df_master.to_csv(master_file, index=False)
    print("=" * 60)
    print(f"SUCCESS: Created Master Dataset at {master_file}")
    print(f"Shape: {df_master.shape[0]} rows x {df_master.shape[1]} columns")
    print(f"Unique Project IDs: {df_master['project_id'].nunique()}")
    print(f"Target Delay Distribution:\n{df_master['target_delayed'].value_counts()}")
    print("=" * 60)
    return df_master

if __name__ == "__main__":
    BASE = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    integrate_datasets(BASE)
