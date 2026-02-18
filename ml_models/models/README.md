# ML Models Directory

This directory contains the trained machine learning models for the renal care management system.

## Model Files

- [`dry_weight_model.pkl`](./dry_weight_model.pkl) - Trained model for dry weight prediction
- [`hb_model.pkl`](./hb_model.pkl) - Trained model for hemoglobin prediction
- [`urr_lightGbm_model.pkl`](./urr_lightGbm_model.pkl) - Trained LightGBM model for URR prediction
- [`urr_model.pkl`](./urr_model.pkl) - Trained model for URR prediction
- [`xgb_model_for_hb.pkl`](./xgb_model_for_hb.pkl) - Trained XGBoost model for hemoglobin prediction

## NOTE

1. Currently, the models are stored in the `ml_models/models` directory.
2. The [`urr_lightGbm_model.pkl`](./urr_lightGbm_model.pkl) and [`xgb_model_for_hb.pkl`](./xgb_model_for_hb.pkl) are not used in the current version of the ML service but are kept for future reference and potential use.

## Usage

The models are automatically loaded by the ML service when predictions are requested.
