"""Feature engineering and transformation pipeline for RiskGuard."""

import pandas as pd
import numpy as np

def extract_project_sector(df: pd.DataFrame) -> pd.Series:
    """Infer infrastructure sector from agency and project descriptions."""
    def assign_sector(row):
        agency = str(row.get("agency", "")).lower()
        name = str(row.get("project_name", "")).lower()
        
        if any(w in agency or w in name for w in ["airport", "aviation", "aai"]):
            return "Civil Aviation"
        elif any(w in agency or w in name for w in ["coal", "ccl", "secl", "wcl", "ecl", "mcl", "bccl", "ncl", "cil"]):
            return "Coal"
        elif any(w in agency or w in name for w in ["rail", "rvnl", "ircon", "dfccil", "krcl", "doubling", "station"]):
            return "Railways"
        elif any(w in agency or w in name for w in ["nhai", "highway", "road", "expressway", "bridge"]):
            return "Road Transport & Highways"
        elif any(w in agency or w in name for w in ["power", "ntpc", "nhpc", "pgcil", "grid", "hydro", "thermal", "solar", "wind"]):
            return "Power & Renewable Energy"
        elif any(w in agency or w in name for w in ["petroleum", "oil", "iocl", "bpcl", "hpcl", "ongc", "gail", "refinery", "pipeline", "gas"]):
            return "Petroleum & Natural Gas"
        elif any(w in agency or w in name for w in ["port", "shipping", "dock", "waterway", "jal marg"]):
            return "Ports & Shipping"
        elif any(w in agency or w in name for w in ["water", "irrigation", "sewerage", "drainage"]):
            return "Water Resources"
        elif any(w in agency or w in name for w in ["telecom", "bsnl", "bbnl", "communication"]):
            return "Telecommunications"
        elif any(w in agency or w in name for w in ["steel", "sail", "rinl"]):
            return "Steel"
        else:
            return "Urban Development & Other"

    return df.apply(assign_sector, axis=1)

def build_project_features(df_paimana: pd.DataFrame) -> pd.DataFrame:
    """Engineer financial, duration, scale, and progress features from PAIMANA projects."""
    df = df_paimana.copy()

    # Sector classification
    df["sector"] = extract_project_sector(df)

    # Cost magnitude category (Small < 500 Cr, Medium 500-1000 Cr, Mega >= 1000 Cr)
    df["is_mega_project"] = (df["original_cost"] >= 1000).astype(int)
    
    # Cost overrun features
    df["has_cost_overrun"] = (df["cost_overrun"] > 0).astype(int)
    
    # Financial commitment ratio: cumulative expenditure relative to original sanction
    df["expenditure_to_original_ratio"] = np.where(
        df["original_cost"] > 0,
        df["expenditure"] / df["original_cost"],
        np.nan
    )

    # Progress velocity / gap: physical progress achieved relative to elapsed duration if available
    df["progress_to_expenditure_gap"] = df["physical_progress"] - (df["expenditure_ratio"] * 100)

    return df
