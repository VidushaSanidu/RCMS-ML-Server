# ML Models Directory

This directory contains the trained machine learning models for the renal care management system.

## Model Files

- `dry_weight_model.pkl` - Trained model for dry weight prediction
- `urr_model.pkl` - Trained model for URR prediction
- `hb_model.pkl` - Trained model for hemoglobin prediction

## Usage

The models are automatically loaded by the ML service when predictions are requested. If model files are not found, dummy models will be used for development and testing.
