# ML Models Directory

This directory contains the trained machine learning models for the renal care management system.

## Model Files Expected:
- `dry_weight_model.pkl` - Trained model for dry weight prediction
- `urr_model.pkl` - Trained model for URR prediction  
- `hb_model.pkl` - Trained model for hemoglobin prediction

## Model Training:
The models should be trained using the notebooks in the `ML_Model/code/` directory and saved as pickle files using joblib.

## Usage:
The models are automatically loaded by the ML service when predictions are requested. If model files are not found, dummy models will be used for development and testing.

## Model Versions:
- All models should be versioned and documented
- Production models should be validated and tested before deployment
- Model metadata and performance metrics should be documented
