# Renal Care Management System - ML Server API Specification

This document provides the complete API specification for the Machine Learning (ML) Server. It is intended for the backend team to integrate the Express.js server with the Django ML server.

---

## 1. General Configuration

* **Default Port**: `8001`
* **Base URL**: `http://localhost:8001` (or `http://ml-server:8001` in a docker environment)
* **Content-Type**: `application/json`
* **CORS**: Configured to allow requests from the Express.js backend (default `http://localhost:5000` or as configured via the `CORS_ALLOWED_ORIGINS` environment variable).

---

## 2. Authentication & Authorization

All prediction endpoints are protected and require a JSON Web Token (JWT) matching the secret on the Express.js backend.

### Headers
Every request to a protected endpoint must include the following header:
```http
Authorization: Bearer <JWT_TOKEN>
```

### JWT Payload Requirements
The JWT token must contain the following claims:
* `id` (String): The unique identifier of the authenticated user.
* `role` (String): The user's role. Allowed roles for prediction endpoints are:
  - `DOCTOR`
  - `NURSE`
  
*Note: Roles are case-insensitive (the server normalizes them to uppercase).*

---

## 3. Endpoints Overview

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| **GET** | `/health/` | No | Server level health check. |
| **GET** | `/api/ml/health/` | No | ML models status health check. |
| **GET** | `/api/ml/models/` | No | Information about available ML models, feature order, and endpoints. |
| **POST** | `/api/ml/predict/dry-weight/` | Yes (Doctor/Nurse) | Predicts if dry weight will change in the next dialysis session. |
| **POST** | `/api/ml/predict/urr/` | Yes (Doctor/Nurse) | Predicts if URR will go to risk region (inadequate) next month. |
| **POST** | `/api/ml/predict/hb/` | Yes (Doctor/Nurse) | Predicts Hemoglobin risk status for next month and returns recommendations. |

---

## 4. Endpoint Specifications

### 4.1. Server Health Check

* **Endpoint**: `/health/`
* **Method**: `GET`
* **Description**: Simple health check to verify if the Django server is online.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "ML Server",
  "message": "Renal Care ML Models API is running"
}
```

---

### 4.2. ML Models Health Check

* **Endpoint**: `/api/ml/health/`
* **Method**: `GET`
* **Description**: Verifies the status of the ML subsystem and lists available models.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "ML Models API",
  "available_models": ["dry_weight", "urr", "hb"],
  "version": "1.0.0"
}
```

---

### 4.3. Models Information

* **Endpoint**: `/api/ml/models/`
* **Method**: `GET`
* **Description**: Retrieves technical details about the available models, including their descriptions, model types, feature order, and internal calculated features.

#### Response (200 OK)
```json
{
  "available_models": {
    "dry_weight": {
      "name": "Dry Weight Change Prediction (LightGBM)",
      "description": "Predicts if dry weight will change in next dialysis session using LightGBM with 19 features from dialysis session data",
      "model_type": "LightGBM with 50 estimators",
      "test_performance": "ROC-AUC: 0.637",
      "data_source": "Dialysis session parameters",
      "input_parameters": [
        "patient_id", "ap", "auf", "bfr", "hd_duration", "puf", "tmp", "vp", 
        "weight_gain", "sys", "dia", "pre_hd_weight", "post_hd_weight", "dry_weight", 
        "weight_gain_avg_3 (optional)", "sys_avg_3 (optional)"
      ],
      "feature_order": [
        "1. SYS_avg_3", "2. VP (mmHg)", "3. AP (mmHg)", "4. Pre HD weight (kg)", 
        "5. Weight_gain_avg_3", "6. SYS (mmHg)", "7. Post HD weight (kg)", 
        "8. Weight_gain_pct", "9. UFR", "10. TMP (mmHg)", "11. DIA (mmHg)", 
        "12. Dry weight (kg)", "13. Weight gain (kg)", "14. AUF (ml)", "15. PUF (ml)", 
        "16. BFR (ml/min)", "17. High_SBP", "18. HD duration (h)", "19. UFR_below_15"
      ],
      "calculated_features": [
        "High_SBP (1 if SYS > 140, else 0)",
        "UFR (PUF / (HD duration × Pre HD weight))",
        "UFR_below_15 (1 if UFR < 15, else 0)",
        "Weight_gain_pct ((Weight gain / Dry weight) × 100)",
        "SYS_avg_3 (3-session rolling average of SYS, uses current if not provided)",
        "Weight_gain_avg_3 (3-session rolling average of Weight gain, uses current if not provided)"
      ],
      "total_features": 19,
      "feature_engineering": "Server automatically calculates 6 derived features from 13 original dialysis parameters",
      "output": "Binary classification: will dry weight change (True/False) with probability and clinical recommendations"
    },
    "urr": {
      "name": "URR Risk Prediction (LightGBM)",
      "description": "Predicts if URR will go to risk region (inadequate) next month using LightGBM model",
      "model_type": "LightGBM",
      "input_parameters": [
        "patient_id (optional)", "albumin", "hb", "s_ca", "serum_na_pre_hd", "urr", 
        "urr_diff", "serum_k_pre_hd", "serum_k_post_hd", "bu_pre_hd", "bu_post_hd", 
        "scr_pre_hd", "scr_post_hd"
      ],
      "feature_order": [
        "1. Albumin (g/L)", "2. Hb (g/dL)", "3. S Ca (mmol/L)", "4. Serum Na Pre-HD (mmol/L)", 
        "5. URR", "6. URR_diff", "7. K_Diff", "8. BU_Diff", "9. SCR_Diff"
      ],
      "calculated_features": [
        "K_Diff (serum_k_pre_hd - serum_k_post_hd)",
        "BU_Diff (bu_pre_hd - bu_post_hd)",
        "SCR_Diff (scr_pre_hd - scr_post_hd)"
      ],
      "total_features": 9,
      "feature_engineering": "Server automatically calculates URR and 3 difference features from laboratory parameters",
      "output": "Binary classification: URR at risk (True/False) with probability, adequacy status and clinical recommendations"
    },
    "hb": {
      "name": "Hemoglobin Risk Prediction (Ensemble)",
      "description": "Predicts if hemoglobin will go to risk region next month using ensemble model",
      "model_type": "Ensemble (XGBoost + LightGBM) with weighted averaging",
      "input_parameters": [
        "albumin", "bu_post_hd", "bu_pre_hd", "s_ca", "scr_post_hd", "scr_pre_hd", 
        "serum_k_post_hd", "serum_k_pre_hd", "serum_na_pre_hd", "ua", "hb_diff", "hb"
      ],
      "feature_order": [
        "1. Albumin (g/L)", "2. S Ca (mmol/L)", "3. Serum Na Pre-HD (mmol/L)", "4. UA (mg/dL)", 
        "5. Hb_diff", "6. Hb (g/dL)", "7. Albumin_BU_Ratio", "8. K_Diff", "9. BU_Diff", "10. SCR_Diff"
      ],
      "calculated_features": [
        "Albumin_BU_Ratio (albumin / (bu_pre_hd + 1))",
        "K_Diff (serum_k_pre_hd - serum_k_post_hd)",
        "BU_Diff (bu_pre_hd - bu_post_hd)",
        "SCR_Diff (scr_pre_hd - scr_post_hd)"
      ],
      "total_features": 10,
      "feature_engineering": "Server automatically calculates 4 derived features from 12 laboratory parameters",
      "ensemble_details": "XGBoost + LightGBM with optimized weights and threshold",
      "output": "Binary classification: Hb at risk (True/False) with probability and clinical recommendations"
    }
  },
  "endpoints": {
    "dry_weight": "/api/ml/predict/dry-weight/",
    "urr": "/api/ml/predict/urr/",
    "hb": "/api/ml/predict/hb/"
  }
}
```

---

### 4.4. Predict Dry Weight Change

* **Endpoint**: `/api/ml/predict/dry-weight/`
* **Method**: `POST`
* **Authentication**: Yes (Required roles: `DOCTOR` or `NURSE`)
* **Description**: Evaluates current dialysis parameters and predicts if the patient's dry weight target will need adjustment in the next hemodialysis session.

#### Request Body Schema (JSON)

| Parameter | Type | Required | Range | Description |
| :--- | :--- | :---: | :---: | :--- |
| `patient_id` | String | Yes | Max 50 chars | Patient identifier |
| `ap` | Float | Yes | `[-500.0, 0.0]` | Arterial Pressure (mmHg) |
| `auf` | Float | Yes | `[0.0, 10000.0]` | Actual Ultrafiltration (ml) |
| `bfr` | Float | Yes | `[100.0, 500.0]` | Blood Flow Rate (ml/min) |
| `hd_duration` | Float | Yes | `[1.0, 8.0]` | Hemodialysis duration (hours) |
| `puf` | Float | Yes | `[0.0, 10000.0]` | Planned Ultrafiltration (ml) |
| `tmp` | Float | Yes | `[0.0, 500.0]` | Transmembrane Pressure (mmHg) |
| `vp` | Float | Yes | `[0.0, 500.0]` | Venous Pressure (mmHg) |
| `weight_gain` | Float | Yes | `[0.0, 10.0]` | Interdialytic weight gain (kg) |
| `sys` | Float | Yes | `[60.0, 250.0]` | Systolic Blood Pressure pre-HD (mmHg) |
| `dia` | Float | Yes | `[40.0, 150.0]` | Diastolic Blood Pressure pre-HD (mmHg) |
| `pre_hd_weight` | Float | Yes | `[20.0, 300.0]` | Pre-dialysis weight (kg) |
| `post_hd_weight` | Float | Yes | `[20.0, 300.0]` | Post-dialysis weight (kg) |
| `dry_weight` | Float | Yes | `[20.0, 300.0]` | Current dry weight target (kg) |
| `weight_gain_avg_3` | Float | No | `[0.0, 10.0]` | 3-session rolling average of weight gain (kg) (Defaults to `weight_gain` if not provided) |
| `sys_avg_3` | Float | No | `[60.0, 250.0]` | 3-session rolling average of Systolic BP (mmHg) (Defaults to `sys` if not provided) |

#### Example Request
```json
{
  "patient_id": "PT_DRY_908",
  "ap": -120.0,
  "auf": 2500.0,
  "bfr": 350.0,
  "hd_duration": 4.0,
  "puf": 2800.0,
  "tmp": 150.0,
  "vp": 80.0,
  "weight_gain": 2.5,
  "sys": 145.0,
  "dia": 85.0,
  "pre_hd_weight": 72.5,
  "post_hd_weight": 70.0,
  "dry_weight": 70.0,
  "weight_gain_avg_3": 2.3,
  "sys_avg_3": 142.0
}
```

#### Response (200 OK)
```json
{
  "patient_id": "PT_DRY_908",
  "dry_weight_change_predicted": true,
  "prediction_status": "Change Expected",
  "change_probability": 0.635,
  "confidence_score": 0.635,
  "current_dry_weight": 70.0,
  "current_weight_gain": 2.5,
  "recommendations": [
    "⚠️ Dry weight adjustment predicted for next session",
    "Monitor fluid status closely and reassess dry weight",
    "High systolic BP detected - consider antihypertensive adjustment"
  ],
  "model_version": "1.0.0",
  "prediction_date": "2026-07-20T12:35:10.892011"
}
```

---

### 4.5. Predict URR Risk

* **Endpoint**: `/api/ml/predict/urr/`
* **Method**: `POST`
* **Authentication**: Yes (Required roles: `DOCTOR` or `NURSE`)
* **Description**: Evaluates clinical laboratory inputs to predict if the Urea Reduction Ratio (URR) will fall into the inadequate/risk region (< 65%) next month.

#### Request Body Schema (JSON)

| Parameter | Type | Required | Range | Description |
| :--- | :--- | :---: | :---: | :--- |
| `albumin` | Float | Yes | `[10.0, 60.0]` | Serum Albumin (g/L) |
| `hb` | Float | Yes | `[2.0, 20.0]` | Hemoglobin (g/dL) |
| `s_ca` | Float | Yes | `[1.5, 10.0]` | Serum Calcium (mmol/L) |
| `serum_na_pre_hd` | Float | Yes | `[120.0, 150.0]` | Serum Sodium Pre-HD (mmol/L) |
| `urr` | Float | Yes | `[30.0, 95.0]` | Current Urea Reduction Ratio (%) |
| `urr_diff` | Float | Yes | `[-30.0, 30.0]` | URR change compared to previous month (%) |
| `serum_k_pre_hd` | Float | Yes | `[2.0, 8.0]` | Serum Potassium Pre-HD (mmol/L) |
| `serum_k_post_hd` | Float | Yes | `[2.0, 7.0]` | Serum Potassium Post-HD (mmol/L) |
| `bu_pre_hd` | Float | Yes | `[10.0, 100.0]` | Blood Urea Pre-HD (mmol/L) |
| `bu_post_hd` | Float | Yes | `[5.0, 50.0]` | Blood Urea Post-HD (mmol/L) |
| `scr_pre_hd` | Float | Yes | `[10.0, 2000.0]` | Serum Creatinine Pre-HD (µmol/L) |
| `scr_post_hd` | Float | Yes | `[10.0, 1500.0]` | Serum Creatinine Post-HD (µmol/L) |
| `patient_id` | String | No | Max 50 chars | Patient identifier |

#### Example Request
```json
{
  "patient_id": "PT_URR_404",
  "albumin": 38.5,
  "hb": 11.2,
  "s_ca": 2.2,
  "serum_na_pre_hd": 136.0,
  "urr": 60.5,
  "urr_diff": -5.0,
  "serum_k_pre_hd": 5.4,
  "serum_k_post_hd": 3.6,
  "bu_pre_hd": 75.0,
  "bu_post_hd": 32.0,
  "scr_pre_hd": 850.0,
  "scr_post_hd": 350.0
}
```

#### Response (200 OK)
```json
{
  "patient_id": "PT_URR_404",
  "urr_risk_predicted": true,
  "risk_status": "At Risk",
  "adequacy_status": "Predicted Inadequate",
  "current_urr": 60.5,
  "target_urr_range": {
    "min": 65.0,
    "max": 100.0
  },
  "risk_probability": 0.781,
  "confidence_score": 0.781,
  "recommendations": [
    "⚠️ Patient predicted to have inadequate URR next month",
    "Current URR below target - dialysis inadequacy detected",
    "Consider increasing treatment time or frequency",
    "Evaluate vascular access function",
    "Inadequate urea reduction - check access flow and dialyzer function"
  ],
  "model_version": "1.0.0",
  "prediction_date": "2026-07-20T12:35:15.912345"
}
```

---

### 4.6. Predict Hemoglobin Risk

* **Endpoint**: `/api/ml/predict/hb/`
* **Method**: `POST`
* **Authentication**: Yes (Required roles: `DOCTOR` or `NURSE`)
* **Description**: Evaluates patient metrics and predicts if their Hemoglobin levels will fall outside the safe/target range ($10.0$ to $12.0$ g/dL) in the next month.

#### Request Body Schema (JSON)

| Parameter | Type | Required | Range | Description |
| :--- | :--- | :---: | :---: | :--- |
| `albumin` | Float | Yes | `[10.0, 60.0]` | Serum Albumin (g/L) |
| `bu_pre_hd` | Float | Yes | `[10.0, 100.0]` | Blood Urea Pre-HD (mmol/L) |
| `bu_post_hd` | Float | Yes | `[5.0, 50.0]` | Blood Urea Post-HD (mmol/L) |
| `s_ca` | Float | Yes | `[1.5, 10.0]` | Serum Calcium (mmol/L) |
| `scr_pre_hd` | Float | Yes | `[10.0, 2000.0]` | Serum Creatinine Pre-HD (µmol/L) |
| `scr_post_hd` | Float | Yes | `[10.0, 1500.0]` | Serum Creatinine Post-HD (µmol/L) |
| `serum_k_pre_hd` | Float | Yes | `[0.0, 8.0]` | Serum Potassium Pre-HD (mmol/L) |
| `serum_k_post_hd` | Float | Yes | `[0.0, 7.0]` | Serum Potassium Post-HD (mmol/L) |
| `serum_na_pre_hd` | Float | Yes | `[0.0, 150.0]` | Serum Sodium Pre-HD (mmol/L) |
| `ua` | Float | Yes | `[0.0, 1000.0]` | Uric Acid (See unit note below) |
| `hb_diff` | Float | Yes | `[-7.0, 7.0]` | Hemoglobin difference compared to last month (g/dL) |
| `hb` | Float | Yes | `[2.0, 20.0]` | Current Hemoglobin (g/dL) |

> [!CAUTION]
> **CRITICAL DEVELOPER NOTE ON URIC ACID (`ua`) UNITS:**
> There is a unit discrepancy between the validator and the ML model for `ua`:
> * The Django Serializer expects values in **$\mu\text{mol/L}$** (range `0-1000` with descriptor `UA (micro mol/L)`).
> * The underlying machine learning model expects values in **$\text{mg/dL}$** (represented as `UA (mg/dL)`).
> * **Standard Conversion**: $1\text{ mg/dL} \approx 59.48\ \mu\text{mol/L}$.
> * **Backend Action**: Until a hotfix is applied, the backend team should convert Uric Acid to **$\text{mg/dL}$** (e.g. values like `5.5` or `7.2`) before making the API call, OR consult the Django team to adjust the serializer to accept and internally convert the inputs.

#### Example Request
```json
{
  "albumin": 34.0,
  "bu_pre_hd": 68.0,
  "bu_post_hd": 22.0,
  "s_ca": 2.0,
  "scr_pre_hd": 900.0,
  "scr_post_hd": 380.0,
  "serum_k_pre_hd": 5.8,
  "serum_k_post_hd": 3.9,
  "serum_na_pre_hd": 135.0,
  "ua": 6.8, 
  "hb_diff": -0.8,
  "hb": 9.2
}
```

#### Response (200 OK)
```json
{
  "hb_risk_predicted": true,
  "risk_status": "At Risk",
  "hb_trend": "Declining to Critical",
  "current_hb": 9.2,
  "target_hb_range": {
    "min": 10.0,
    "max": 12.0
  },
  "risk_probability": 0.812,
  "confidence_score": 0.812,
  "recommendations": [
    "⚠️ Patient predicted to enter Hb risk zone next month",
    "Current Hb below target - urgent intervention needed",
    "Consider increasing EPO dose or iron supplementation",
    "Low albumin - nutritional counseling recommended",
    "Low calcium - consider calcium supplementation",
    "High potassium - dietary restriction advised"
  ],
  "model_version": "1.0.0",
  "prediction_date": "2026-07-20T12:35:20.100982"
}
```

---

## 5. Error Responses

All endpoints return a uniform error structure in case of validation failures, unauthorized access, or server faults.

### 5.1. Validation Error (400 Bad Request)
Returned when payload parameters are missing, of the wrong type, or fail boundary checks.

```json
{
  "error": "Invalid input data",
  "message": "Please check the input parameters",
  "details": {
    "ap": [
      "Ensure this value is greater than or equal to -500."
    ],
    "hb": [
      "This field is required."
    ]
  }
}
```

### 5.2. Unauthorized (401 Unauthorized)
Returned when the `Authorization` header is missing, is not format-compliant, or contains an expired/invalid token.

```json
{
  "error": "Authentication required",
  "message": "Please provide a valid JWT token in Authorization header"
}
```

### 5.3. Forbidden (403 Forbidden)
Returned when the JWT contains a valid user token, but the user's role claim is not authorized for the prediction endpoint (i.e. not `DOCTOR` or `NURSE`).

```json
{
  "error": "Insufficient permissions",
  "message": "This endpoint requires one of the following roles: DOCTOR, NURSE"
}
```

### 5.4. Internal Server Error (500 Internal Server Error)
Returned when an unhandled exception or model loading issue occurs inside the ML server.

```json
{
  "error": "Prediction failed",
  "message": "An error occurred during prediction. Please try again."
}
```

---

## 6. Known Potential Issues / Integration Gotchas

1. **Mac OS Deployment Dependency (`libomp`)**:
   When launching the ML server on macOS, loading the models can crash with a dynamic linker error for `libomp.dylib`. If this happens, run `brew install libomp` on the host system.
2. **Missing Request Logging Middleware**:
   The code has a debug middleware named `RequestLoggingMiddleware` located in `ml_models/middleware/request_logging.py`, but it is **not** registered in the `MIDDLEWARE` setting in `settings.py`. It will not run unless added.
3. **URR Model Call Inconsistency**:
   The prediction views currently trigger `model.predict([features])` with a nested list but `model.predict_proba(X)` with a pandas DataFrame for URR, which could trigger warnings in LightGBM due to feature name discrepancies. This does not impact the output values but is an inconsistency.
