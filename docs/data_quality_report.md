# RiskGuard: Data Quality & Validation Report 📊

**Pipeline:** Member 2 Data Processing & Integration  
**Master Dataset:** `data/processed/master/riskguard_master.csv`  
**Evaluation Date:** March 2026

---

## 1. Dataset Scale & Invariant Verification

| Metric | Target / Requirement | Observed Value | Status |
|---|---|---|---|
| **Total PAIMANA Projects Extracted** | ~1,941 projects | **1,941** | ✅ Exact Match |
| **Project Code Uniqueness** | 100% unique | **1,941 unique IDs (0 duplicates)** | ✅ Passed |
| **Merge Granularity Invariant** | Exactly $N_{master} == 1,941$ | **1,941 rows** | ✅ Passed |
| **Row Count Expansion on Joins** | 0 duplicate project rows | **0 duplicates across all 5 joins** | ✅ Passed |
| **Master Dataset Dimensionality** | Project-level consolidated | **1,941 rows × 65 columns** | ✅ Passed |
| **Train / Test Split Ratio** | 80% / 20% Stratified | **1,552 train (80%) / 389 test (20%)** | ✅ Passed |

---

## 2. Geographic Entity Matching Rates

Secondary datasets were pre-aggregated to state level and joined onto the PAIMANA project backbone using canonical standardized state names (`state_std`):

| Secondary Dataset | Source State Rows | Matched PAIMANA Projects | Match Percentage | Handling of Unmatched (Multi-States / UTs) |
|---|---|---|---|---|
| **Census Demographics (2011)** | 34 states | 1,848 / 1,941 | **95.2%** | Multi-States and small UTs imputed using national median |
| **Court Pendency Statistics** | 36 states | 1,852 / 1,941 | **95.4%** | Multi-States imputed using national median |
| **Power Infrastructure (RBI)** | 35 states | 1,848 / 1,941 | **95.2%** | Multi-States imputed using national median |
| **Road Connectivity (MoRTH BRS)**| 36 states | 1,852 / 1,941 | **95.4%** | Multi-States imputed using national median |
| **Gujarat Private Property (RERA)**| 32 districts (Gujarat)| 142 Gujarat projects | **100% of Gujarat projects** | Non-Gujarat projects explicitly assigned $0$ |

---

## 3. Target Class Balance (`target_delayed`)

- **Definition:** $1$ if `schedule_delay_days > 0` (or `revised_completion_date > original_completion_date`), else $0$.
- **Delayed Projects ($1$):** **1,196 (61.6%)**
- **On-Time / Early Projects ($0$):** **745 (38.4%)**
- **Stratification Verification:**
  - `y_train`: 956 Delayed (61.6%), 596 On-time (38.4%)
  - `y_test`: 240 Delayed (61.7%), 149 On-time (38.3%)
  - The class ratio is preserved to within 0.1% across splits.

---

## 4. Data Leakage Audit Checklist

- [x] **No Direct Target Derivatives in Features:** `schedule_delay_days` has been strictly removed from `X_train` and `X_test`.
- [x] **No Project Identifiers in Features:** `project_id`, `legacy_ocms_code`, `project_name`, and `agency` are excluded from input vectors.
- [x] **No Raw Post-Hoc Timestamps:** Dates (`original_completion_date`, `revised_completion_date`, etc.) are removed from $X$; only baseline `planned_duration_days` is retained.
- [x] **Strict Train-Only Fitting:** The `preprocessor.joblib` pipeline (imputation + standard scaling + one-hot encoding) was fit **exclusively on `X_train`** and applied downstream to `X_test`.

---

## 5. Domain-Specific Limitations

1. **Gujarat RERA Scope:** The private property dataset covers projects registered under Gujarat RERA only. While it provides excellent local commercial market context for Gujarat-based infrastructure developments, it has not been imputed to non-Gujarat states.
2. **Census Baseline Epoch:** The Census data reflects 2011 decennial figures, which serve as a high-fidelity relative demographic baseline across districts/states, though not dynamic annual telemetry.
3. **Power Time Horizon:** RBI power statistics benchmark the 2020-21 fiscal year, capturing mature state grid capacities.
