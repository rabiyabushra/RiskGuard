# RiskGuard Backend & API Reference Specification 🚀
### Member 5 Deliverable: Asynchronous FastAPI Service, Database Integration & Gemini Reasoning

---

## 1. Architecture & Pipeline Flow

The RiskGuard backend acts as the central orchestration bridge connecting the data layer, the machine learning inference core, the generative AI advisor, and the frontend web dashboard:

```
                  ┌─────────────────────────────────────────┐
                  │        React + Tailwind Frontend        │
                  │              (Member 6)                 │
                  └────────────────────┬────────────────────┘
                                       │ HTTP / JSON
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │             FastAPI Backend             │
                  │            (backend/main.py)            │
                  └───────────┬───────────────┬─────────────┘
                              │               │
            ┌─────────────────┴──────┐        └─────────────────┐
            ▼                        ▼                          ▼
   ┌─────────────────┐     ┌───────────────────┐      ┌──────────────────┐
   │ MongoDB Storage │     │  AI/ML & SHAP     │      │ Google Gemini    │
   │ (motor_asyncio) │     │  Inference Engine │      │ Generative AI    │
   ├─────────────────┤     ├───────────────────┤      ├──────────────────┤
   │ • projects      │     │ • best_model.pkl  │      │ • gemini-1.5-    │
   │ • predictions   │     │ • preprocessor.pkl│      │   flash          │
   │ • explanations  │     │ • TreeExplainer   │      │ • Context-aware  │
   │ (with fallback) │     │ • risk_analysis.py│      │   prompts        │
   └─────────────────┘     └───────────────────┘      └──────────────────┘
```

---

## 2. Environment Configuration

Create a `.env` file inside `backend/` or the project root. Refer to `backend/.env.example`:

```bash
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=riskguard_db

# Google Gemini API
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...

# Server Settings
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=*
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10+
- MongoDB 6.0+ (Optional: in-memory/file fallback mode activates automatically if MongoDB is offline)

### Install Dependencies
```bash
cd RiskGuard
pip install -r backend/requirements.txt
```

### Database Seeding
To populate MongoDB with Member 2's 1,941 processed infrastructure projects, Member 4's risk scores, and SHAP explanation profiles:
```bash
python backend/seed_db.py --uri mongodb://localhost:27017 --db riskguard_db
```

### Start the FastAPI Server
```bash
# From RiskGuard root directory:
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI Swagger docs will be available at:
👉 **`http://localhost:8000/docs`**

---

## 4. API Endpoints Reference

### A. System & Health

#### `GET /`
- **Purpose**: Confirms service availability and reports active modules.
- **Sample Response**:
  ```json
  {
    "service": "RiskGuard API",
    "version": "1.0.0",
    "status": "online",
    "documentation": "/docs",
    "modules": [
      "projects",
      "prediction",
      "risk-analysis",
      "shap-explainability",
      "gemini-recommendations"
    ]
  }
  ```

#### `GET /health`
- **Purpose**: Checks database connectivity, model loading, and pipeline readiness.
- **Sample Response**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "model_loaded": true,
    "preprocessor_loaded": true
  }
  ```

---

### B. Project Management

#### `GET /projects`
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `limit`: Number of items per page (default: 20, max: 100)
  - `state`: Filter by state name (e.g. `Gujarat`, `Assam`, `Andhra Pradesh`)
  - `sector`: Filter by sector (e.g. `Civil Aviation`, `Road Transport & Highways`)
  - `risk_category`: Filter by risk tier (`LOW`, `MEDIUM`, `HIGH`)
- **Sample Response**:
  ```json
  {
    "total": 1941,
    "page": 1,
    "limit": 2,
    "data_source": "mongodb",
    "projects": [
      {
        "project_id": "612786",
        "project_name": "Construction of New Domestic Terminal Building at Kadapa Airport",
        "agency": "Airport Authority of India [AAI]",
        "sector": "Civil Aviation",
        "state": "Andhra Pradesh",
        "original_cost": 265.91,
        "revised_cost": 265.91,
        "expenditure": 120.19,
        "physical_progress": 60.0,
        "delay_probability": 0.8862,
        "risk_score": 88.62,
        "risk_category": "HIGH"
      }
    ]
  }
  ```

#### `GET /projects/{project_id}`
- **Purpose**: Retrieve complete dossier for a specific project.
- **Response**: Full project record or `404 Not Found`.

#### `POST /projects`
- **Purpose**: Create or register a new project.
- **Request Body**: `ProjectInputSchema`

---

### C. Real ML Prediction

#### `POST /predict`
- **Purpose**: Executes real-time machine learning inference through `best_model.pkl` and `preprocessor.pkl`.
- **Request Body**:
  ```json
  {
    "project_name": "New Expressway Corridor Package 3",
    "sector": "Road Transport & Highways",
    "state": "Gujarat",
    "original_cost": 450.0,
    "revised_cost": 520.0,
    "expenditure": 180.0,
    "physical_progress": 25.0,
    "planned_duration_days": 1095
  }
  ```
- **Response**:
  ```json
  {
    "project_id": "PRJ-9A8B7C6D",
    "project_name": "New Expressway Corridor Package 3",
    "prediction": 1,
    "delay_probability": 0.8421,
    "risk_score": 84.21,
    "risk_category": "HIGH"
  }
  ```

---

### D. Risk Analysis & Thresholds

#### `GET /risk-analysis/{project_id}`
- **Purpose**: Retrieves calibrated risk scores, operational category, and threshold reference.
- **Sample Response**:
  ```json
  {
    "project_id": "612786",
    "project_name": "Construction of New Domestic Terminal Building at Kadapa Airport",
    "delay_probability": 0.8862,
    "risk_score": 88.62,
    "risk_category": "HIGH",
    "thresholds": {
      "LOW": "< 35.0",
      "MEDIUM": "35.0 - 64.99",
      "HIGH": ">= 65.0"
    },
    "top_risk_factors": [
      "planned_duration_days",
      "expenditure_ratio",
      "avg_household_size"
    ]
  }
  ```

---

### E. Explainable AI (SHAP)

#### `GET /projects/{project_id}/explanation`
- **Purpose**: Exposes mathematical SHAP feature attributions, top positive/negative drivers, and objective human-readable narratives.
- **Sample Response**:
  ```json
  {
    "project_id": "612786",
    "project_name": "Construction of New Domestic Terminal Building at Kadapa Airport",
    "delay_probability": 0.8862,
    "risk_score": 88.62,
    "risk_category": "HIGH",
    "base_value": 0.48,
    "top_risk_increasing_factors": [
      {
        "feature": "planned_duration_days",
        "shap_value": 1.1809,
        "feature_value": -0.4636
      },
      {
        "feature": "expenditure_ratio",
        "shap_value": 0.2935,
        "feature_value": 0.2217
      }
    ],
    "top_risk_reducing_factors": [
      {
        "feature": "cost_overrun",
        "shap_value": -0.1305,
        "feature_value": -0.0982
      }
    ],
    "narrative_explanations": [
      "Planned Duration Days is strongly contributing toward higher predicted project delay risk.",
      "Expenditure Ratio is strongly contributing toward higher predicted project delay risk.",
      "Cost Overrun is contributing toward lowering the predicted delay risk."
    ]
  }
  ```

#### `GET /shap/global`
- **Purpose**: Returns top global delay drivers ranked by mean absolute SHAP across all projects.

---

### F. Generative AI Recommendations (Gemini)

#### `POST /recommendations`
- **Purpose**: Synthesizes delay probability, risk score, risk category, and identified SHAP drivers into an analytical prompt sent to Google Gemini 1.5 Flash.
- **Request Body**:
  ```json
  {
    "project_id": "612786"
  }
  ```
  *(Or optionally supply custom `project_data` directly in request body)*
- **Sample Response**:
  ```json
  {
    "project_id": "612786",
    "project_name": "Construction of New Domestic Terminal Building at Kadapa Airport",
    "delay_probability": 0.8862,
    "risk_score": 88.62,
    "risk_category": "HIGH",
    "top_risk_factors": [
      "Planned Duration Days",
      "Expenditure Ratio",
      "Avg Household Size"
    ],
    "recommendations": [
      "Conduct an immediate joint financial-physical milestone audit to reconcile the expenditure-to-progress ratio.",
      "Implement critical-path fast-tracking and enforce contractor liquidated damages clauses for lagging terminal sub-packages.",
      "Engage with regional administration to streamline site-clearance and utility relocation bottlenecks."
    ],
    "model_used": "gemini-1.5-flash",
    "status": "gemini_live"
  }
  ```

---

## 5. Resilience & Offline Fallback Architecture

To guarantee high development availability during hackathon demonstrations:
1. **Database Fallback**: If MongoDB is offline, project listing and lookup endpoints automatically query the precomputed master dataset (`risk_predictions.csv`), ensuring zero API downtime.
2. **Gemini Fallback**: If `GEMINI_API_KEY` is not supplied, the recommendation service provides deterministic, domain-heuristic recommendations derived from the project's risk category and SHAP factors, clearly signaling `"status": "offline_fallback"`.
