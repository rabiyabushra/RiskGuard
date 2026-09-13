# RiskGuard 🛡️
### Data-Driven Infrastructure Project Delay Prediction and Risk Assessment System

RiskGuard is an end-to-end intelligent infrastructure risk management platform. It synthesizes central infrastructure project monitoring data with regional demographic, power infrastructure, legal pendency, connectivity (road network), and private real-estate project density to predict schedule delays, classify project risk levels, and deliver actionable explanations using SHAP.

---

## 📂 Project Architecture

```
RiskGuard/
│
├── data/
│   ├── raw/                  # Pristine raw datasets (read-only)
│   │   ├── paimana/          # MoSPI PAIMANA Flash Report (March 2026)
│   │   ├── census/           # Census of India 2011 administrative & demographic data
│   │   ├── private_property/ # Gujarat RERA private project dataset
│   │   ├── court/            # Judicial pendency & judge shortfall
│   │   ├── power/            # RBI state-wise power requirement & availability
│   │   └── roads/            # Basic Road Statistics (BRS 2018-19) connectivity
│   │
│   ├── interim/              # Normalized extraction outputs
│   │
│   └── processed/            # Cleaned, standardized, aggregated datasets
│       ├── paimana/          # Project-level infrastructure data
│       ├── census/           # State/district demographic features
│       ├── private_property/ # Gujarat district real-estate metrics
│       ├── court/            # State legal risk indicators
│       ├── power/            # State power capacity & gap
│       ├── roads/            # State road density & length
│       └── master/           # riskguard_master.csv (unified project dataset)
│
├── notebooks/                # Reproducible Jupyter analysis pipelines
│   ├── 01_data_exploration.ipynb
│   ├── 02_data_preprocessing.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_data_integration.ipynb
│   ├── 05_model_training.ipynb
│   └── 06_model_explainability.ipynb
│
├── src/                      # Modular production codebase
│   ├── preprocessing/        # Extraction and cleaning per domain
│   ├── features/             # Feature engineering & transformations
│   ├── models/               # Training, validation, hyperparameter tuning
│   └── explainability/       # SHAP explanations & feature attribution
│
├── models/                   # Serialized ML models (XGBoost, Random Forest, etc.)
├── backend/                  # FastAPI REST service (future phase)
├── frontend/                 # React + Leaflet GIS dashboard (future phase)
├── docs/                     # Data dictionary & system architecture documentation
└── tests/                    # Unit and integration test suites
```

---

## 🚀 Quickstart

1. Clone or navigate to the repository:
   ```bash
   cd RiskGuard
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the exploration notebook:
   ```bash
   jupyter notebook notebooks/01_data_exploration.ipynb
   ```
