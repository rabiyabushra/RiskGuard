# RiskGuard: Project Risk Analysis & Scoring Methodology 🛡️

**System:** RiskGuard Infrastructure Risk Engine  
**Champion Model:** `XGBClassifier` (persisted at `models/best_model.pkl`)  
**Evaluation ROC-AUC:** 0.8924 | **Test Partition:** $N=389$

---

## 1. Risk Score Definition

RiskGuard converts raw machine learning delay probabilities into an intuitive **0 to 100 Risk Score**:

$$\text{risk\_score} = \text{delay\_probability} \times 100$$

- **0.00 Probability** $\rightarrow$ **0 Risk Score** (Negligible risk of schedule slippage)
- **0.50 Probability** $\rightarrow$ **50 Risk Score** (Moderate / borderline delay likelihood)
- **1.00 Probability** $\rightarrow$ **100 Risk Score** (Critical risk of major project delay)

> [!NOTE]
> The risk score reflects the model's calibrated confidence that an infrastructure project will fail to meet its baseline scheduled Date of Commissioning (DoC). It is not identical to historical completion rates or overall cost overrun severity.

---

## 2. Calibrated Risk Category Thresholds

To assist infrastructure monitoring officers, line ministry engineers, and project management units (PMUs), continuous risk scores are segmented into three operational tiers:

| Risk Category | Risk Score Range | Delay Probability Range | Operational Definition & Recommended Action |
|---|---|---|---|
| **LOW** | $[0.0, 35.0)$ | $[0.00, 0.35)$ | **On-Track:** Physical milestones and expenditures align with baseline schedules. Routine quarterly monitoring. |
| **MEDIUM** | $[35.0, 65.0)$ | $[0.35, 0.65)$ | **Watchlist:** Moderate schedule friction detected (e.g. expenditure lag, regional power grid deficit). Monthly reviews. |
| **HIGH** | $[65.0, 100.0]$ | $[0.65, 1.00]$ | **Critical Intervention:** High probability of substantial delay. Root-cause audit and site liaison team required. |

### Portfolio Distribution (N = 1,941 Projects):
- **HIGH:** **1,095 projects (56.41%)**
- **LOW:** **562 projects (28.95%)**
- **MEDIUM:** **284 projects (14.63%)**

*Note:* This distribution aligns with the historical reality of Indian central infrastructure projects monitored under MoSPI PAIMANA, where over 60% of projects experience milestone slippage.

---

## 3. Explainable AI Methodology (SHAP)

RiskGuard utilizes **SHAP (SHapley Additive exPlanations)** based on cooperative game theory to explain model outputs:

$$\hat{f}(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$

Where:
- $\phi_0$ is the base expected model value ($0.4799$ in log-odds/margin space).
- $\phi_i(x)$ is the Shapley value for feature $i$, quantifying its directional contribution.
- $M = 97$ input features.

Because the champion model is an XGBoost decision tree ensemble, we implement **TreeSHAP** via `shap.TreeExplainer`, which guarantees:
1. **Local Accuracy (Additivity)**: The sum of individual feature contributions plus the baseline equals the model output.
2. **Missingness Preservation**: Features not active in a project do not receive arbitrary attribution.
3. **Consistency**: A feature that increases the model's delay probability receives a positive SHAP value across all trees.

---

## 4. Global Feature Attribution (Top Delay Drivers)

Aggregating mean absolute SHAP values across all test projects ($N=389$) reveals the most influential factors driving delay predictions:

| Rank | Feature Name | Mean \|SHAP\| Value | Impact Direction & Narrative Interpretation |
|---|---|---|---|
| 1 | `physical_progress` | 0.9761 | Primary pacing signal; low progress relative to project age strongly drives delay risk. |
| 2 | `planned_duration_days` | 0.5205 | Longer planned multi-year timelines inherently face higher uncertainty and risk. |
| 3 | `expenditure_ratio` | 0.3389 | Low fund utilization indicates contractor mobilization or land clearance roadblocks. |
| 4 | `expenditure` | 0.1742 | Scale of capital outlay; mega outlays require complex inter-agency coordination. |
| 5 | `cost_overrun` | 0.1562 | Financial inflation is strongly coupled with physical schedule slippage. |
| 6 | `expenditure_to_original_ratio` | 0.1034 | Ratio of spent capital to initial sanction reflects budget escalation pressures. |
| 7 | `progress_to_expenditure_gap` | 0.0902 | Mismatch between money spent and physical progress achieved on site. |
| 8 | `revised_cost` | 0.0788 | Scale of revised financial commitment. |
| 9 | `total_road_length` | 0.0733 | Regional transport logistics capacity; remote regions face logistics delays. |
| 10 | `cost_overrun_percent` | 0.0642 | Normalized percentage budget escalation. |

---

## 5. Distinction Between Statistical Attribution and Real-World Causation

> [!CAUTION]
> **Important Epistemic Distinction:**
> SHAP measures how individual input features **contribute to the machine learning model's prediction**, NOT real-world physical causality.
> 
> - **Permitted Narrative Phrasing:**
>   - *"High cost overrun is contributing strongly to the model's predicted delay risk."*
>   - *"Low physical progress is increasing the predicted likelihood of delay."*
> - **Prohibited Narrative Phrasing:**
>   - *"High cost overrun caused the project to be delayed."*
>   - *"Low road density caused contractor delivery failure."*
