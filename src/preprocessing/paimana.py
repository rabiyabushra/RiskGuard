"""PAIMANA PDF extraction and cleaning module.

Extracts all ongoing projects from Table 6 (March 2026 Flash Report)
with exact 1:1 project verification, numeric sanitization, date parsing,
and schedule/cost variance feature calculations.
"""

import os
import re
import pandas as pd
import numpy as np
import pypdf

def extract_paimana_projects(pdf_path: str) -> pd.DataFrame:
    """Extract Table 6 project records from the PAIMANA Flash Report PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PAIMANA PDF not found at {pdf_path}")

    reader = pypdf.PdfReader(pdf_path)
    pages_text = [reader.pages[pno].extract_text() or "" for pno in range(54, 156)]
    full_text = "\n".join(pages_text)

    # Clean wrapped parentheses
    normalized = re.sub(r'\(\s*\n\s*([^()\n]+)\s*\n\s*\)', r'(\1)', full_text)
    normalized = re.sub(r'\(\s+([^()\n]+)\s+\)', r'(\1)', normalized)
    normalized = re.sub(r'\(\s*\n\s*([^()\n]+)\)', r'(\1)', normalized)
    normalized = re.sub(r'\(([^\n()]+)\s*\n\s*\)', r'(\1)', normalized)

    skip_patterns = [
        r'^All Ongoing Projects$', r'^MARCH 2026$', r'^Project Assessment, Infrastructure Monitoring',
        r'^\(PAIMANA\)$', r'^Page \d+$', r'^For details visit:', r'^Sl\.No$', r'^Project Name$',
        r'^\(Agency\)$', r'^\(Project Code\)', r'^State$', r'^Date of Approval', r'^\(Start Date\)',
        r'^MM/YYYY$', r'^Orignal/Target DoC', r'^\(Revised DoC\)$', r'^Orignal Cost', r'^Revised Cost',
        r'^in Rs\. Crore$', r'^Cumulative$', r'^Expenditure$', r'^Physical Progress', r'^\(%\)$',
        r'^Total \(\d+\)', r'^\*+$', r'^Ministry of ', r'^Sector -'
    ]

    cleaned_lines = []
    for l in normalized.splitlines():
        s = l.strip()
        if not s or any(re.match(p, s, re.IGNORECASE) for p in skip_patterns):
            continue
        cleaned_lines.append(s)

    # Identify project code anchors: (Code) preceded by (Agency) and followed by (LegacyCode)
    true_codes = []
    for i in range(1, len(cleaned_lines) - 1):
        l = cleaned_lines[i]
        m = re.match(r'^\((\d{5,8})\)$', l)
        if m:
            prev = cleaned_lines[i - 1]
            nxt = cleaned_lines[i + 1]
            if prev.startswith('(') and prev.endswith(')') and re.search(r'[A-Za-z]', prev):
                if nxt.startswith('(') and nxt.endswith(')'):
                    true_codes.append((i, m.group(1), prev, nxt))

    records = []
    for k, (idx, code, agency_str, legacy_str) in enumerate(true_codes):
        agency = agency_str.strip('()')
        legacy_code = legacy_str.strip('()')

        # Project name is between previous project end (or serial number) and agency
        name_lines = []
        j = idx - 2
        while j >= 0 and j >= idx - 10:
            line_val = cleaned_lines[j]
            if re.match(r'^\d{1,4}$', line_val):
                break
            name_lines.insert(0, line_val)
            j -= 1
        project_name = " ".join(name_lines).strip()

        # Remaining tokens for this project up to next project's agency
        next_idx = true_codes[k + 1][0] - 1 if k + 1 < len(true_codes) else len(cleaned_lines)
        tail_lines = cleaned_lines[idx + 2: next_idx]

        # Extract state (until date or cost pattern is reached)
        state_tokens = []
        val_idx = 0
        while val_idx < len(tail_lines):
            line_val = tail_lines[val_idx]
            if re.match(r'^(?:\d{2}/\d{4}|NA|-|\(\d{2}/\d{4}\)|\(-?\d+(?:\.\d+)?\))$', line_val):
                break
            state_tokens.append(line_val)
            val_idx += 1

        state = " ".join(state_tokens).strip()
        remaining = tail_lines[val_idx:]

        # Values: date_of_approval, start_date, original_doc, revised_doc, original_cost, revised_cost, expenditure, progress
        rec = {
            "project_id": code,
            "legacy_ocms_code": legacy_code if legacy_code != '-' else None,
            "project_name": project_name,
            "agency": agency,
            "state": state,
            "date_of_approval": remaining[0] if len(remaining) > 0 else None,
            "start_date": remaining[1].strip('()') if len(remaining) > 1 else None,
            "original_completion_date": remaining[2] if len(remaining) > 2 else None,
            "revised_completion_date": remaining[3].strip('()') if len(remaining) > 3 else None,
            "original_cost": remaining[4] if len(remaining) > 4 else None,
            "revised_cost": remaining[5].strip('()') if len(remaining) > 5 else None,
            "expenditure": remaining[6] if len(remaining) > 6 else None,
            "physical_progress": remaining[7] if len(remaining) > 7 else None,
        }
        records.append(rec)

    df = pd.DataFrame(records)
    return df

def clean_paimana_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data types, parse dates, and engineer schedule/cost overrun features."""
    df = df.copy()

    # Clean numeric fields
    numeric_cols = ["original_cost", "revised_cost", "expenditure", "physical_progress"]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace('₹', '', regex=False).str.strip('() ')
        df[col] = pd.to_numeric(df[col].replace(['-', 'NA', 'None', 'nan', ''], np.nan), errors='coerce')

    # Parse date fields
    date_cols = ["date_of_approval", "start_date", "original_completion_date", "revised_completion_date"]
    for col in date_cols:
        clean_date_str = df[col].astype(str).str.strip('() ')
        clean_date_str = clean_date_str.replace(['-', 'NA', 'None', 'nan', ''], np.nan)
        df[col + "_dt"] = pd.to_datetime(clean_date_str, format='%m/%Y', errors='coerce')

    # Baseline cost overrun
    df["cost_overrun"] = df["revised_cost"] - df["original_cost"]
    df["cost_overrun_percent"] = np.where(
        df["original_cost"] > 0,
        (df["cost_overrun"] / df["original_cost"]) * 100,
        np.nan
    )

    # Expenditure ratio
    effective_cost = np.where(df["revised_cost"].notnull() & (df["revised_cost"] > 0), df["revised_cost"], df["original_cost"])
    df["expenditure_ratio"] = np.where(
        effective_cost > 0,
        (df["expenditure"] / effective_cost),
        np.nan
    )

    # Schedule delay days (revised_doc - original_doc)
    delay_delta = (df["revised_completion_date_dt"] - df["original_completion_date_dt"]).dt.days
    df["schedule_delay_days"] = np.where(
        df["revised_completion_date_dt"].notnull() & df["original_completion_date_dt"].notnull(),
        delay_delta,
        0
    )

    # Target variable definition:
    # 1 if schedule_delay_days > 0, else 0
    df["target_delayed"] = (df["schedule_delay_days"] > 0).astype(int)

    # Planned duration in days (original_completion - start_date)
    duration_delta = (df["original_completion_date_dt"] - df["start_date_dt"]).dt.days
    df["planned_duration_days"] = np.where(
        df["original_completion_date_dt"].notnull() & df["start_date_dt"].notnull(),
        duration_delta,
        np.nan
    )

    return df

def run_paimana_pipeline(raw_pdf_path: str, output_dir: str):
    """Execute end-to-end PAIMANA extraction and cleaning."""
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 60)
    print("PAIMANA EXTRACTION PIPELINE")
    print("=" * 60)

    print(f"Reading and extracting Table 6 from: {raw_pdf_path}")
    df_raw = extract_paimana_projects(raw_pdf_path)
    raw_csv = os.path.join(output_dir, "paimana_projects.csv")
    df_raw.to_csv(raw_csv, index=False)
    print(f"Saved extracted project table: {raw_csv} ({len(df_raw)} records)")

    print("Cleaning extracted records and engineering schedule/cost features...")
    df_clean = clean_paimana_data(df_raw)
    clean_csv = os.path.join(output_dir, "paimana_clean.csv")
    df_clean.to_csv(clean_csv, index=False)
    print(f"Saved cleaned project table: {clean_csv} ({len(df_clean)} records)")
    print(f"Delay target distribution:\n{df_clean['target_delayed'].value_counts(normalize=True)}")
    print("PAIMANA pipeline finished successfully.")
    return df_clean

if __name__ == "__main__":
    BASE_DIR = r"c:\Users\RABIYA BUSHRA\OneDrive\Attachments\Desktop\SIH\Implementation\RiskGuard"
    pdf = os.path.join(BASE_DIR, "data", "raw", "paimana", "FlashReport_March_2026.pdf")
    out = os.path.join(BASE_DIR, "data", "processed", "paimana")
    run_paimana_pipeline(pdf, out)
