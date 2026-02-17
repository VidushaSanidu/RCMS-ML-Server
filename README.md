# ML Server for Renal Care Management

A Django-based ML server providing machine learning model predictions for renal care management.

## Features

- **JWT Authentication**: Secure endpoints using the same JWT tokens as Express.js backend
- **Role-based Access**: Restrict prediction endpoints to doctors and nurses only
- **Dry Weight Change Prediction**: Predicts if dry weight will change in next dialysis session
- **URR Risk Prediction**: Predicts if URR will go to risk region (inadequate) next month  
- **Hemoglobin Risk Prediction**: Predicts if Hb will go to risk region next month with clinical recommendations

## API Endpoints

### Health Check
```
GET /health/ - Server health check
GET /api/ml/health/ - ML models health check
GET /api/ml/models/ - Information about available models
```

### Predictions
```
POST /api/ml/predict/dry-weight/ - Predict dry weight change
POST /api/ml/predict/urr/ - Predict URR risk
POST /api/ml/predict/hb/ - Predict hemoglobin risk
```

## Authentication

The ML server uses JWT authentication compatible with the Express.js backend.

### Protected Endpoints
All prediction endpoints require authentication:
- `POST /api/ml/predict/dry-weight/` - Requires DOCTOR or NURSE role
- `POST /api/ml/predict/urr/` - Requires DOCTOR or NURSE role  
- `POST /api/ml/predict/hb/` - Requires DOCTOR or NURSE role

### Public Endpoints
These endpoints don't require authentication:
- `GET /health/` - Server health check
- `GET /api/ml/health/` - ML models health check
- `GET /api/ml/models/` - Information about available models

### Authorization Header
Include JWT token in requests:
```
Authorization: Bearer <your-jwt-token>
```

## Quick Start

### Option 1: Use the startup script (Windows)
```cmd
# For Command Prompt
start_server.bat

# For PowerShell
.\start_server.ps1
```

### Option 2: Manual setup
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start the server:
```bash
python manage.py runserver 8001
```

## Testing

Run the API tests:
```bash
python test_api.py
```

## Usage

The server runs on port 8001 and provides REST API endpoints for ML predictions.

### Example API Calls

#### Dry Weight Prediction
```bash
curl -X POST http://localhost:8001/api/ml/predict/dry-weight/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "patient_id": "RHD_THP_001",
    "age": 45,
    "gender": "Male",
    "height": 170.5,
    "weight": 70.2,
    "systolic_bp": 140,
    "diastolic_bp": 90,
    "pre_dialysis_weight": 72.5,
    "post_dialysis_weight": 69.8,
    "ultrafiltration_volume": 2.7,
    "dialysis_duration": 4.0
  }'
```

#### URR Prediction
```bash
curl -X POST http://localhost:8001/api/ml/predict/urr/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "patient_id": "RHD_THP_002",
    "pre_dialysis_urea": 120,
    "dialysis_duration": 4.0,
    "blood_flow_rate": 300,
    "dialysate_flow_rate": 500,
    "ultrafiltration_rate": 800,
    "access_type": "fistula",
    "kt_v": 1.4
  }'
```

#### Hemoglobin Prediction
```bash
curl -X POST http://localhost:8001/api/ml/predict/hb/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "patient_id": "RHD_THP_003",
    "albumin": 35.2,
    "bu_post_hd": 8.5,
    "bu_pre_hd": 25.3,
    "s_ca": 2.3,
    "scr_post_hd": 450,
    "scr_pre_hd": 890,
    "serum_k_post_hd": 3.8,
    "serum_k_pre_hd": 5.2,
    "serum_na_pre_hd": 138,
    "ua": 6.8,
    "hb_diff": -0.5,
    "hb": 9.5
  }'
```

## Model Files

Place trained model files in `ml_models/models/` directory:
- `dry_weight_model.pkl`
- `urr_model.pkl` 
- `hb_model.pkl`

If model files are not found, dummy models will be used for development.

## Integration with Express.js Backend

The ML server is designed to work alongside the Express.js backend:
- Express.js backend runs on port 3000
- ML server runs on port 8001
- CORS is configured to allow requests from the Express.js server

## Architecture

```
Frontend (React) → Express.js Backend (port 3000) → ML Server (port 8001)
                        ↓
                  MongoDB Database
```

## Project Structure

```
ML_Server/
├── ml_server/              # Django project
│   ├── __init__.py
│   ├── settings.py         # Django settings with CORS, REST framework
│   ├── urls.py             # Main URL routing
│   ├── wsgi.py             # WSGI application
│   └── asgi.py             # ASGI application
├── ml_models/              # Django app for ML models
│   ├── __init__.py
│   ├── apps.py             # App configuration
│   ├── views.py            # API views for predictions
│   ├── serializers.py      # DRF serializers for validation
│   ├── services.py         # ML prediction services
│   ├── urls.py             # App URL patterns
│   └── models/             # ML model files directory
│       ├── README.md
│       ├── dry_weight_model.pkl    # (to be added)
│       ├── urr_model.pkl          # (to be added)
│       └── hb_model.pkl           # (to be added)
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── start_server.bat       # Windows batch startup script
├── start_server.ps1       # PowerShell startup script
├── test_api.py           # API testing script
└── README.md             # This file
```

## Development Notes

- The server uses dummy models for development if real model files are not available
- JWT authentication uses the same secret as the Express.js backend for token compatibility
- Prediction endpoints require DOCTOR or NURSE roles for access
- Public endpoints (health checks, models info) don't require authentication
- Comprehensive error handling and logging
- REST API with proper HTTP status codes
- Input validation using Django REST Framework serializers
- CORS configured for integration with Express.js backend
- Swagger/OpenAPI documentation support (via drf-spectacular)

## Security Configuration

### Environment Variables
Make sure to set the same JWT_SECRET in both servers:

**Express.js Backend (.env):**
```
JWT_SECRET=your-super-secret-jwt-key-here-change-in-production
```

**ML Server (.env):**
```
JWT_SECRET=your-super-secret-jwt-key-here-change-in-production
```

### Role-based Access Control
- **DOCTOR**: Full access to all prediction endpoints
- **NURSE**: Full access to all prediction endpoints  
- **ADMIN**: Currently not required for ML predictions (can be added if needed)

### Token Requirements
- Valid JWT token in Authorization header
- Token must contain 'id' and 'role' fields
- Token must be signed with the correct JWT_SECRET
