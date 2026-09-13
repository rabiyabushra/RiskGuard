# RiskGuard: Model Evaluation & Benchmark Report 📈

**Evaluation Partition:** Untouched Test Split (`X_test.csv`, $N=389$)  
**Target Variable:** `target_delayed` ($1 = 	ext{Delayed}$, $0 = 	ext{On-Time}$)  
**Positive Class Prevalence in Test Set:** 240 / 389 (61.7%)

---

## 1. Comparative Model Performance Summary

All models were tuned via 5-fold cross-validation exclusively on the training partition ($N=1,552$) and evaluated on the identical, untouched test partition ($N=389$):

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---|---|---|---|
| **Logistic Regression (Baseline)** | 0.7969 | 0.8108 | 0.8750 | 0.8417 | 0.8641 |
| **Random Forest (Tuned)** | 0.7995 | 0.8022 | 0.8958 | 0.8465 | 0.8785 |
| **XGBoost (Champion)** | **0.8123** | **0.8249** | **0.8833** | **0.8531** | **0.8924** |

---

## 2. Champion Model Selection Rationale

**Selected Champion Model:** `XGBoostClassifier`  
**Artifact:** `models/best_model.pkl`

### Key Selection Drivers:
1. **Superior Discriminative Capability (ROC-AUC: 0.8924)**:  
   XGBoost demonstrates the highest area under the receiver operating characteristic curve, outperforming tuned Random Forest (0.8785) and Logistic Regression (0.8641). This guarantees optimal probability ranking across varying risk thresholds.
2. **Balanced Recall & Precision (F1: 0.8531)**:  
   Detects delayed infrastructure projects with high sensitivity (88.3% recall) while minimizing false alarms (82.5% precision).
3. **Handling Non-Linear Interactions**:  
   Gradient boosting effectively models compound interactions between project duration, cost overruns, state judicial pendency, and regional power deficits.

---

## 3. Evaluation Artifacts Generated

- **Confusion Matrices:**
  - `docs/reports/model_evaluation/logistic_regression_confusion_matrix.png`
  - `docs/reports/model_evaluation/random_forest_confusion_matrix.png`
  - `docs/reports/model_evaluation/xgboost_confusion_matrix.png`
- **ROC Curves:**
  - `docs/reports/model_evaluation/roc_curve_comparison.png`
- **Model Comparison:**
  - `docs/reports/model_evaluation/model_comparison.png`
- **Feature Importance:**
  - `docs/reports/model_evaluation/feature_importance.png`
