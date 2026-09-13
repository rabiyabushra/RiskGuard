# RiskGuard: Data Dictionary 📖

This document describes all features present in the master infrastructure project dataset (`riskguard_master.csv`) and training datasets (`X_train.csv`).

---

## 1. Project Identifiers & Metadata (PAIMANA)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations / Leakage Risk |
|---|---|---|---|---|---|
| `project_id` | MoSPI PAIMANA | String / Int | Identifier | Primary numeric project identifier from PAIMANA IPM portal | Excluded from ML training to avoid memorization |
| `legacy_ocms_code` | MoSPI PAIMANA | String | Identifier | Legacy Online Computerized Monitoring System alphanumeric code | Excluded from ML training |
| `project_name` | MoSPI PAIMANA | String | Description | Text description of the infrastructure development project | Excluded from ML training; used in UI/Search |
| `agency` | MoSPI PAIMANA | String | Category | Central implementing agency (e.g. AAI, NHAI, NTPC, RVNL) | Encoded via sector grouping |
| `state` | MoSPI PAIMANA | String | Location | Raw state name as published in PAIMANA Flash Report | Normalized to `state_std` |
| `state_std` | Preprocessing | String | Join Key / Feature | Canonical standardized state name | Encoded via One-Hot encoding |
| `sector` | Feature Eng. | String | Categorical Feature | Inferred infrastructure sector (Aviation, Coal, Railways, etc.) | High predictive power; no leakage |

---

## 2. Project Cost & Physical Progress Features

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations / Leakage Risk |
|---|---|---|---|---|---|
| `original_cost` | MoSPI PAIMANA | Float (₹ Cr) | Input Feature | Baseline government sanction cost | Valid baseline predictor |
| `revised_cost` | MoSPI PAIMANA | Float (₹ Cr) | Operational Feature | Latest approved or anticipated project cost | May be updated after delays occur |
| `cost_overrun` | Feature Eng. | Float (₹ Cr) | Financial Feature | `revised_cost - original_cost` | High correlation with delay severity |
| `cost_overrun_percent` | Feature Eng. | Float (%) | Financial Feature | `(cost_overrun / original_cost) * 100` | Normalized financial inflation |
| `expenditure` | MoSPI PAIMANA | Float (₹ Cr) | Operational Feature | Cumulative funds disbursed to date | Real-time tracking feature |
| `expenditure_ratio` | Feature Eng. | Float (Ratio) | Operational Feature | `expenditure / revised_cost` | Fund utilization progress |
| `physical_progress` | MoSPI PAIMANA | Float (%) | Operational Feature | Cumulative on-site physical execution completion | Self-reported by implementing agency |
| `is_mega_project` | Feature Eng. | Binary (0/1) | Input Feature | $1$ if `original_cost >= 1000` Cr, else $0$ | Proxy for procurement/governance complexity |

---

## 3. Project Schedule & Delay Target

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations / Leakage Risk |
|---|---|---|---|---|---|
| `date_of_approval` | MoSPI PAIMANA | Date (MM/YYYY)| Timeline | Month and year of formal project approval | Parsed to datetime |
| `start_date` | MoSPI PAIMANA | Date (MM/YYYY)| Timeline | Month and year of ground work commencement | Parsed to datetime |
| `original_completion_date` | MoSPI PAIMANA | Date (MM/YYYY)| Timeline | Baseline approved Date of Commissioning (DoC) | Parsed to datetime |
| `revised_completion_date` | MoSPI PAIMANA | Date (MM/YYYY)| Timeline | Anticipated or revised commissioning date | Parsed to datetime |
| `planned_duration_days` | Feature Eng. | Integer (Days) | Input Feature | `(original_completion_date - start_date)` in days | Excellent baseline scale feature; zero leakage |
| `schedule_delay_days` | Feature Eng. | Integer (Days) | Outcome Metric | `(revised_completion_date - original_completion_date)` | **EXCLUDED FROM X** (Target proxy leakage) |
| `target_delayed` | Feature Eng. | Binary (0/1) | **Target Variable**| $1$ if `schedule_delay_days > 0`, else $0$ | Ground truth classification target |

---

## 4. Demographic Features (Census 2011)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations |
|---|---|---|---|---|---|
| `population` | Census 2011 | Integer | Input Feature | State-level total population (`TOT_P`, `TRU=Total`) | Reflects regional scale |
| `households` | Census 2011 | Integer | Input Feature | Total occupied residential households (`No_HH`) | Correlated with population |
| `female_population_ratio` | Census 2011 | Float (Ratio) | Input Feature | `TOT_F / TOT_P` | Gender diversity index |
| `literacy_rate` | Census 2011 | Float (%) | Input Feature | `(P_LIT / TOT_P) * 100` | Human capital & literacy proxy |
| `worker_rate` | Census 2011 | Float (%) | Input Feature | `(TOT_WORK_P / TOT_P) * 100` | Labor force participation rate |
| `non_worker_rate` | Census 2011 | Float (%) | Input Feature | `(NON_WORK_P / TOT_P) * 100` | Dependent population ratio |
| `avg_household_size` | Census 2011 | Float | Input Feature | `population / households` | Household density |

---

## 5. Judicial & Legal Risk Features (Court Pendency)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations |
|---|---|---|---|---|---|
| `budget_per_capita_judiciary` | India Justice Report | Float (₹) | Input Feature | Per capita public expenditure on state courts | Legal system resourcing |
| `pop_per_high_court_judge` | India Justice Report | Integer | Input Feature | Population per active High Court judge | Superior court dispute resolution delay |
| `pop_per_lower_court_judge` | India Justice Report | Integer | Input Feature | Population per active subordinate court judge | Land acquisition litigation bottlenecks |
| `courthall_shortfall_pct` | India Justice Report | Float (%) | Input Feature | Deficit of courtrooms relative to sanctioned judges | Physical legal infrastructure shortfall |
| `case_clearance_rate_hc` | India Justice Report | Float (%) | Input Feature | Cases disposed / cases filed in High Court | Disposal velocity |
| `case_clearance_rate_lower`| India Justice Report | Float (%) | Input Feature | Cases disposed / cases filed in Subordinate Courts | Dispute resolution capacity |
| `legal_pressure_index` | Feature Eng. | Float (0–1) | Input Feature | Weighted combination of judge burden and shortfall | Compound legal risk |

---

## 6. Power Infrastructure Features (RBI Database)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations |
|---|---|---|---|---|---|
| `power_requirement` | RBI Infrastructure | Float (Cr Units) | Input Feature | State-wide annual electricity requirement (2020-21)| Energy demand volume |
| `power_availability` | RBI Infrastructure | Float (Cr Units) | Input Feature | State-wide annual electricity supplied (2020-21) | Grid energy delivery |
| `power_gap` | Feature Eng. | Float (Cr Units) | Input Feature | `power_requirement - power_availability` | Energy deficit / surplus |
| `power_gap_percent` | Feature Eng. | Float (%) | Input Feature | `(power_gap / power_requirement) * 100` | Relative electrical deficit |
| `installed_power_capacity`| RBI Infrastructure | Float (MW) | Input Feature | Total generation capacity installed in the state | Regional energy infrastructure |
| `power_per_capita` | RBI Infrastructure | Float (kWh) | Input Feature | Per capita electricity consumption/availability | Industrial development proxy |

---

## 7. Road Connectivity Features (MoRTH BRS 2018-19)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations |
|---|---|---|---|---|---|
| `total_road_length` | MoRTH BRS | Float (km) | Input Feature | Total classified road network length in state | Geographic connectivity |
| `national_highways_length`| MoRTH BRS | Float (km) | Input Feature | Total length of National Highways in state | Freight trunk capacity |
| `state_highways_length` | MoRTH BRS | Float (km) | Input Feature | Total length of State Highways in state | Intra-state connectivity |
| `road_density_per_1000sqkm`| MoRTH BRS | Float | Input Feature | Road network length per 1,000 sq. km land area | Spatial accessibility |
| `surfaced_road_ratio` | Feature Eng. | Float (Ratio) | Input Feature | `surfaced_road_length / total_road_brs31` | All-weather transport reliability |
| `road_length_per_1000pop` | MoRTH BRS | Float | Input Feature | Road kilometers per 1,000 residents | Connectivity per capita |

---

## 8. Gujarat Private Property Context (Gujarat RERA)

| Feature Name | Source | Data Type | Role | Calculation / Description | Limitations |
|---|---|---|---|---|---|
| `gujarat_private_project_count` | Gujarat RERA | Integer | Input Feature | Total private real-estate projects in Gujarat | Strictly Gujarat-specific ($0$ elsewhere) |
| `gujarat_private_total_cost_cr`| Gujarat RERA | Float (₹ Cr) | Input Feature | Total private investment in Gujarat projects | Captures competitive resource pressure |
| `gujarat_private_avg_cost_sqft` | Gujarat RERA | Float (₹/sqft)| Input Feature | Median cost per square foot in Gujarat real estate | Regional construction cost index |
