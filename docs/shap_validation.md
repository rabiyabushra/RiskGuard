# RiskGuard: SHAP Validation & Technical Audit Report 🔍

**Validation Engine:** Member 4 Risk Analysis & Explainability  
**Target Model:** `XGBClassifier` (`models/best_model.pkl`)  
**Audited Partition:** Test Partition (`X_test.csv`, $N=389$)

---

## 1. Audit Checklist & Integrity Checks

| Validation Check | Method / Criteria | Result | Status |
|---|---|---|---|
| **Explainer Selection** | Appropriate for tree ensemble model | `shap.TreeExplainer` initialized | ✅ Passed |
| **Sample Completeness** | SHAP values generated for all test samples | $N = 389$ rows | ✅ Passed |
| **Dimension Matching** | SHAP matrix dimensions match input $X$ | Exactly `(389, 97)` | ✅ Passed |
| **Feature Name Alignment** | Output columns map 1:1 to transformed feature names | 97 matching names, 0 missing | ✅ Passed |
| **Base Value Consistency** | Base expected value equals training sample prior | $\phi_0 = 0.4799$ | ✅ Passed |
| **Local Additivity** | $\phi_0 + \sum \phi_i \approx \text{margin output}$ | Verified within machine epsilon ($10^{-5}$) | ✅ Passed |
| **Individual Attribution** | Positive and negative factors correctly segregated | $\text{SHAP} > 0$ vs. $\text{SHAP} < 0$ | ✅ Passed |

---

## 2. Detailed Verification Methodology

1. **Dimensional Integrity:**
   - Input matrix shape: `(389, 97)`
   - Computed SHAP matrix shape: `(389, 97)`
   - Every column in `X_test` (e.g. `physical_progress`, `planned_duration_days`, `sector_Civil Aviation`, `state_std_Odisha`) maps directly to its respective column index in the SHAP attribution array.

2. **Additivity Verification:**
   - For a sample of 10 test records, the sum of SHAP values plus the base expected value was compared against the model's raw decision function (`margin output` before logistic sigmoid transformation).
   - In 100% of tested instances, the discrepancy was $< 10^{-5}$, verifying complete numerical additivity.

3. **Ranking Consistency:**
   - Top positive contributors correctly correspond to features with the largest positive $\phi_i$ values.
   - Top negative contributors correctly correspond to features with the most negative $\phi_i$ values.

---

## 3. Limitations & Deployment Guidelines

1. **Feature Interaction Approximations:**
   - TreeSHAP accurately computes individual feature marginals, but higher-order interactions are summarized into the main feature attributions.
2. **Correlated Feature Attributions:**
   - Highly correlated pairs (e.g., `cost_overrun` and `cost_overrun_percent`, or `population` and `households`) share attribution across their joint decision paths. Both are preserved in the data dictionary for domain transparency.
3. **Non-Causal Disclaimer:**
   - Attribution outputs must always be displayed with non-causal language on the frontend dashboard to ensure project directors understand that recommendations are decision-support heuristics, not deterministic proof of physical delay causes.
