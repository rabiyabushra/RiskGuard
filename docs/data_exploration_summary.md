# RiskGuard: Data Exploration & Schema Audit Report

**Date:** March 2026  
**System:** RiskGuard — Data-Driven Infrastructure Project Delay Prediction & Risk Assessment System  
**Audited Directory:** `RiskGuard/data/raw/`

---

## Executive Summary

Before undertaking cleaning, transformation, and feature engineering, all 8 raw datasets provided for RiskGuard were ingested, profiled, and audited. This audit characterizes file sizes, dimensions, data schemas, missingness patterns, candidate join keys, target variables, and domain nuances.

| Dataset Name | Raw File Path | Format & Size | Rows / Cols | Administrative / Entity Granularity | Candidate Primary / Join Key |
|---|---|---|---|---|---|
| **PAIMANA Infrastructure** | `data/raw/paimana/FlashReport_March_2026.pdf` | PDF (6.8 MB) | Table 6: 102 pages (~1,941 projects) | Project-level | `project_code` / `ocms_code` |
| **Census 2011** | `data/raw/census/2011-IndiaStateDistSbDistTwn-0000.xlsx` | Excel (16 MB) | 28,389 rows, 94 cols | State, District, Sub-district, Town | `State`, `District`, `Name` |
| **Private Property (Gujarat)** | `data/raw/private_property/ProjectInfo_Gujarat.csv` | CSV (7.3 MB) | 14,507 rows, 44 cols | Project-level (Gujarat RERA only) | `projectRegId`, `distName` |
| **Court Pendency** | `data/raw/court/Pendency of Court Cases in India.csv` | CSV (2 KB) | 37 rows, 8 cols | State/UT level (36 States/UTs + India) | `State/UT` |
| **Power Infrastructure** | `data/raw/power/India_Statewise_Power_Infrastructure_Data_RBI.csv` | CSV (24 KB) | 612 rows, 6 cols | State-level annual time series (2004-2021) | `State/Union Territory`, `Year` |
| **Roads (Surfaced)** | `data/raw/roads/Road_Transport_BRS_2018-19_Annexure3_1.csv` | CSV (926 B) | 37 rows, 4 cols | State/UT level | `Name of State / UT` |
| **Roads (Density / Area)** | `data/raw/roads/Road_Transport_BRS_2018-19_Annexure7_9b.csv` | CSV (3.8 KB) | 36 rows, 16 cols | State/UT level | `Name of the States` |
| **Roads (Length / Pop)** | `data/raw/roads/Road_Transport_BRS_2018-19_Annexure7_9c.csv` | CSV (3.3 KB) | 36 rows, 16 cols | State/UT level | `Name of the States` |

---

## 1. PAIMANA Infrastructure Projects

- **Source:** Ministry of Statistics and Programme Implementation (MoSPI) / PAIMANA.
- **File:** `FlashReport_March_2026.pdf` (158 pages total).
- **Core Section:** Table 6 ("All Ongoing Projects"), spanning **Page 55 to Page 156**.
- **Scope:** Projects costing Rs. 150 Crore and above across 17 Central Line Ministries and Departments.
- **Key Columns Detected:**
  - `Sl.No`: Serial number index per ministry section.
  - `Project Name`: Detailed infrastructure project description.
  - `Agency`: Implementing organization (e.g. Airport Authority of India, SECL, NHAI, RVNL, etc.).
  - `Project Code`: Unique numerical project identifier (e.g., `612786`).
  - `Legacy OCMS Code`: Secondary reference code (e.g., `N04000106`).
  - `State`: Location of project execution (State name, or `Multi-States (...)`).
  - `Date of Approval`: Month and year of sanction (`MM/YYYY`).
  - `Start Date`: Work commencement date (`MM/YYYY`).
  - `Original/Target DoC`: Baseline scheduled Date of Commissioning (`MM/YYYY`).
  - `Revised DoC`: Anticipated or revised completion date (`MM/YYYY` or `-`).
  - `Original Cost`: Baseline sanction cost (Rs. Crore).
  - `Revised Cost`: Approved or anticipated revised cost (Rs. Crore).
  - `Cumulative Expenditure`: Money expended to date (Rs. Crore).
  - `Physical Progress`: Self-reported completion percentage (`%`).
- **Derived Fields for ML Target & Features:**
  - `target_delayed`: Binary indicator ($1$ if `revised_doc > original_doc` or `schedule_delay_days > 0`, else $0$).
  - `cost_overrun`: `revised_cost - original_cost`.
  - `cost_overrun_percent`: `(cost_overrun / original_cost) * 100`.
  - `expenditure_ratio`: `cumulative_expenditure / revised_cost`.
  - `schedule_delay_days`: Calendar day differential between baseline and revised target dates.
  - `progress_gap`: Ratio or differential between expected timeline elapsed and actual `physical_progress`.
- **Anomalies & Data Notice:**
  - Line breaks inside parenthesized fields (e.g., `(\n 01/2024 \n)`).
  - Explicit official MoSPI footnote on Page 156 states projects `618051`, `618307`, `618930`, `619065`, `619113`, and `705410` are temporarily excluded from certain tables due to expenditure verification.

---

## 2. Census of India (2011)

- **Source:** Office of the Registrar General & Census Commissioner, India.
- **File:** `2011-IndiaStateDistSbDistTwn-0000.xlsx` (Sheet: `Data`).
- **Dimensions:** 28,389 rows, 94 columns. 0 duplicates.
- **Hierarchy (`Level` column):**
  - `India` (National summary): 3 rows (`TRU` = Total, Rural, Urban).
  - `STATE` (State/UT summaries): 105 rows.
  - `DISTRICT` (District summaries): 1,920 rows (640 distinct districts across Total/Rural/Urban).
  - `SUB-DISTRICT` (Tehsils/Talukas): 17,772 rows.
  - `TOWN` (Statutory/Census towns): 8,589 rows.
- **Mandatory Filtering Rule:** To prevent massive population duplication, we isolate `Level == 'DISTRICT'` (or `STATE`) with `TRU == 'Total'`.
- **Key Demographic Features:**
  - `No_HH`: Number of households.
  - `TOT_P`, `TOT_M`, `TOT_F`: Population totals and gender breakdown.
  - `P_LIT`, `M_LIT`, `F_LIT`: Literate population (used to compute `literacy_rate`).
  - `TOT_WORK_P`, `MAINWORK_P`, `MARGWORK_P`, `NON_WORK_P`: Workforce composition (used to compute `worker_rate` and `non_worker_rate`).

---

## 3. Private Property / Real-Estate Context (Gujarat RERA)

- **Source:** Gujarat Real Estate Regulatory Authority.
- **File:** `ProjectInfo_Gujarat.csv`.
- **Dimensions:** 14,507 rows, 44 columns. 0 duplicates.
- **Geographic Boundary:** Strictly Gujarat across 35 districts (`distName` e.g., Ahmedabad, Surat, Vadodara, Rajkot, Bhavnagar, etc.).
- **Strict Analytical Rule:** This data provides local market pressure context for projects sited in Gujarat. It must **never** be imputed as national proxy data for other states.
- **Key Fields:**
  - Identifiers: `projectRegId`, `projectName`, `promoterName`.
  - Financials: `totalEstimatedCost`, `totalIncurredCost`, `totalLandCost`, `totalDevelopCost`.
  - Physical Scale: `totalUnits`, `bookedUnits`, `totalSquareFootBuild`, `totalCarpetArea_form3A`.
  - Missingness: `totalAreaOfLand` (39.9% missing), `pinCode` (46.9% missing), `tPNo` (51.4% missing).

---

## 4. Court Pendency & Judicial Capacity

- **Source:** India Justice Report / National Judicial Data.
- **File:** `Pendency of Court Cases in India.csv`.
- **Dimensions:** 37 rows, 8 columns (36 States/UTs + 1 aggregate India row).
- **Features Extracted:**
  - `budget_per_capita_judiciary`: Budget allocated per citizen.
  - `pop_per_high_court_judge`: Population burden per High Court judge.
  - `pop_per_lower_court_judge`: Population burden per subordinate court judge.
  - `courthall_shortfall_pct`: Infrastructure deficiency of courtrooms. (Contains 1 missing value and negative strings e.g. `"- 4.0"` denoting surplus courtrooms).
  - `case_clearance_rate_hc` & `case_clearance_rate_lower`: Efficiency of case disposal.

---

## 5. Power Infrastructure (RBI)

- **Source:** Reserve Bank of India (RBI) Database on Indian Economy.
- **File:** `India_Statewise_Power_Infrastructure_Data_RBI.csv`.
- **Dimensions:** 612 rows, 6 columns across 17 fiscal years (`2004-05` to `2020-21`).
- **Cleaning Requirement:** The raw table stores missing observations as hyphen `"-"` strings, causing numeric columns to load as `object` dtype.
- **Derived Benchmark Metrics (Latest Year `2020-21`):**
  - `power_requirement`: Net energy required (Crore Units).
  - `power_availability`: Net energy available (Crore Units).
  - `power_gap`: `power_requirement - power_availability`.
  - `installed_power_capacity`: Total installed generation capacity (MW).
  - `power_per_capita`: Per capita electricity availability (kWh).

---

## 6. Road Transport Connectivity (BRS 2018-19)

- **Source:** Ministry of Road Transport and Highways (MoRTH) — Basic Road Statistics.
- **Files:**
  - `Road_Transport_BRS_2018-19_Annexure3_1.csv` (Surfaced vs. Unsurfaced total road network).
  - `Road_Transport_BRS_2018-19_Annexure7_9b.csv` (Road density per 1,000 sq km by highway type: National, State, District, Rural, Urban, Project).
  - `Road_Transport_BRS_2018-19_Annexure7_9c.csv` (Road length per 1,000 population by highway type).
- **Consolidation Plan:** Join all 3 annexures into `roads_clean.csv` using sanitized state names (stripping trailing whitespace, `(*)`, and `$`).

---

## 7. Data Integration & Master Dataset Architecture

```
PAIMANA Project Backbone (Project-level, ~1,941 rows)
   │
   ├── [Join Key: State] ───────► Census State Demographics (Level='STATE', TRU='Total')
   │                              - population, households, literacy_rate, worker_rate
   │
   ├── [Join Key: State] ───────► RBI Power Infrastructure (Year='2020-21')
   │                              - power_requirement, power_gap, installed_capacity
   │
   ├── [Join Key: State] ───────► MoRTH Road Connectivity (BRS 2018-19)
   │                              - total_road_length, road_density, highway_density
   │
   ├── [Join Key: State] ───────► Judicial Pendency & Legal Risk
   │                              - pop_per_judge, courthall_shortfall, clearance_rate
   │
   └── [Join Key: State='Gujarat' & District] ──► Aggregated Gujarat RERA Context
                                                  - private_project_count, private_project_cost
                                                  (0 or NaN for non-Gujarat states)
```

---

## 8. Quality Control & Anti-Leakage Rules

1. **Target Isolation:** `target_delayed` is determined strictly from baseline schedule targets (`original_doc`, `revised_doc`, `schedule_delay_days`). Post-hoc operational metrics will not be leaked into input features.
2. **Pristine Raw Preservation:** `data/raw/` remains 100% untouched. All transformations output strictly to `data/interim/` and `data/processed/`.
3. **No Artificial Rows:** Aggregations occur on secondary tables prior to joining so that PAIMANA project rows are never multiplied.
