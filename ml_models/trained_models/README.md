# Trained Models for Renal Care Management System

This directory contains the trained machine learning models for the Renal Care Management System. These models are used by the ML service to make predictions based on the input data.

## Available Models

- [`dry_weight_model.pkl`](./dry_weight_model.pkl) - Trained model for dry weight prediction
- [`hb_model.pkl`](./hb_model.pkl) - Trained model for hemoglobin prediction
- [`urr_model.pkl`](./urr_model.pkl) - Trained model for URR prediction

## Additional Models (Not Currently Used)

The [`urr_lightGbm_model.pkl`](./urr_lightGbm_model.pkl) and [`xgb_model_for_hb.pkl`](./xgb_model_for_hb.pkl) are not used in the current version of the ML service but are kept for future reference and potential use.

## Usage

The models are automatically loaded by the ML service when predictions are requested.

> NOTE: The `ml_models/trained_models/` dictionary is hardcoded in the [`services.py`](../services.py) file in the `MLModelManager` class, so if you add new models, make sure to update the code accordingly. also, if you want to move the models to a different directory, you will need to update the paths in the code as well.
