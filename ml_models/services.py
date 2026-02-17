import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MLModelManager:
    """
    Manager class for loading and managing ML models
    """
    
    def __init__(self):
        self.models = {}
        self.model_versions = {}
        self.model_paths = {
            'dry_weight': 'models/dry_weight_model.pkl',
            'urr': 'models/urr_model.pkl',
            'hb': 'models/hb_model.pkl'
        }
        
    def load_model(self, model_name: str):
        """Load a specific ML model or ensemble bundle"""
        if model_name not in self.models:
            model_path = os.path.join(os.path.dirname(__file__), self.model_paths[model_name])
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            try:
                loaded_object = joblib.load(model_path)
            except Exception as e:
                raise ValueError(f"Failed to load model from {model_path}: {str(e)}")
            
            # Handle different model formats
            if hasattr(loaded_object, 'predict'):
                # Single model object
                self.models[model_name] = loaded_object
            elif isinstance(loaded_object, dict):
                # Ensemble model bundle (like your notebook approach)
                if model_name == 'hb':
                    # Strictly validate ensemble structure for Hb model
                    required_keys = ['xgb', 'lgbm', 'weights', 'threshold']
                    missing_keys = [key for key in required_keys if key not in loaded_object]
                    if missing_keys:
                        raise ValueError(f"Invalid ensemble model for {model_name}. Missing keys: {missing_keys}. Required: {required_keys}")
                    
                    # Validate models are proper ML models
                    if not hasattr(loaded_object['xgb'], 'predict_proba'):
                        raise ValueError(f"XGB model in ensemble does not have predict_proba method")
                    if not hasattr(loaded_object['lgbm'], 'predict_proba'):
                        raise ValueError(f"LGBM model in ensemble does not have predict_proba method")
                    
                    # Store the complete ensemble bundle
                    self.models[model_name] = loaded_object
                    logger.info(f"Loaded ensemble model for {model_name} with XGB + LGBM (weights: {loaded_object['weights']}, threshold: {loaded_object['threshold']})")
                else:
                    # For other models, allow dict but warn
                    self.models[model_name] = loaded_object
                    logger.warning(f"Loaded dict object for {model_name}: {list(loaded_object.keys())}")
            else:
                raise ValueError(f"Loaded object for {model_name} is not a valid ML model (type: {type(loaded_object)}). Expected an object with 'predict' method or ensemble dict.")
            
            self.model_versions[model_name] = "1.0.0"  # Default version
            logger.info(f"Successfully loaded model: {model_name}")
        
        return self.models[model_name]
    
    def get_model_version(self, model_name: str) -> str:
        """Get the version of a loaded model"""
        return self.model_versions.get(model_name, "unknown")





class DryWeightPredictor:
    """
    Dry weight prediction service using LightGBM with dialysis session data
    """
    
    def __init__(self, model_manager: MLModelManager):
        self.model_manager = model_manager
        self.model_name = 'dry_weight'
        
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if dry weight will change in next session using LightGBM model
        """
        try:
            # Load model
            model = self.model_manager.load_model(self.model_name)
            
            # Prepare features
            features = self._prepare_features(input_data)

            print(features)
            
            # Convert features to DataFrame for LightGBM compatibility
            import pandas as pd
            feature_names = [
                'SYS_avg_3', 'VP (mmHg)', 'AP (mmHg)', 'Pre HD weight (kg)',
                'Weight_gain_avg_3', 'SYS (mmHg)', 'Post HD weight (kg)', 'Weight_gain_pct',
                'UFR', 'TMP (mmHg)', 'DIA (mmHg)', 'Dry weight (kg)',
                'Weight gain (kg)', 'AUF (ml)', 'PUF (ml)', 'BFR (ml/min)',
                'High_SBP', 'HD duration (h)', 'UFR_below_15'
            ]
            X = pd.DataFrame([features], columns=feature_names)
            
            # Make classification prediction
            prediction = model.predict(X)[0]
            
            # Get prediction probabilities
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)[0]
                confidence = max(probabilities)
                risk_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                raise ValueError(f"Model {self.model_name} does not support probability predictions")
            
            # Interpret prediction
            will_change = bool(prediction)
            status = "Change Expected" if will_change else "Stable"
            
            # Generate recommendations
            recommendations = self._generate_recommendations(input_data, will_change)
            
            return {
                'patient_id': input_data['patient_id'],
                'dry_weight_change_predicted': will_change,
                'prediction_status': status,
                'change_probability': round(float(risk_probability), 3),
                'confidence_score': round(float(confidence), 3),
                'current_dry_weight': float(input_data['dry_weight']),
                'current_weight_gain': float(input_data['weight_gain']),
                'recommendations': recommendations,
                'model_version': self.model_manager.get_model_version(self.model_name),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in dry weight prediction: {str(e)}")
            raise
    
    def _prepare_features(self, input_data: Dict[str, Any]) -> List[float]:
        """Prepare 19 features for the LightGBM dry weight model"""
        
        # Calculate derived features
        high_sbp = 1 if input_data['sys'] > 140 else 0
        
        # UFR calculation: PUF (ml) / (HD duration (h) × Pre HD weight (kg))
        hd_duration_hours = input_data['hd_duration']
        pre_hd_weight = input_data['pre_hd_weight']
        ufr = input_data['puf'] / (hd_duration_hours * pre_hd_weight) if (hd_duration_hours * pre_hd_weight) > 0 else 0
        
        # UFR_below_15
        ufr_below_15 = 1 if ufr < 15 else 0
        
        # Weight_gain_pct = (Weight gain (kg) / Dry weight (kg)) × 100
        weight_gain_pct = (input_data['weight_gain'] / input_data['dry_weight']) * 100 if input_data['dry_weight'] > 0 else 0
        
        # Rolling averages (use provided values or defaults if not available)
        weight_gain_avg_3 = input_data.get('weight_gain_avg_3', input_data['weight_gain'])
        sys_avg_3 = input_data.get('sys_avg_3', input_data['sys'])
        
        # Prepare feature array in the exact order expected by the model
        features = [
            sys_avg_3,                           # SYS_avg_3 (rolling average)
            input_data['vp'],                    # VP (mmHg)
            input_data['ap'],                    # AP (mmHg)
            input_data['pre_hd_weight'],         # Pre HD weight (kg)
            weight_gain_avg_3,                   # Weight_gain_avg_3 (rolling average)
            input_data['sys'],                   # SYS (mmHg)
            input_data['post_hd_weight'],        # Post HD weight (kg)
            weight_gain_pct,                     # Weight_gain_pct (calculated)
            ufr,                                 # UFR (calculated)
            input_data['tmp'],                   # TMP (mmHg)
            input_data['dia'],                   # DIA (mmHg)
            input_data['dry_weight'],            # Dry weight (kg)
            input_data['weight_gain'],           # Weight gain (kg)
            input_data['auf'],                   # AUF (ml)
            input_data['puf'],                   # PUF (ml)
            input_data['bfr'],                   # BFR (ml/min)
            high_sbp,                            # High_SBP (calculated)
            input_data['hd_duration'],           # HD duration (h)
            ufr_below_15                         # UFR_below_15 (calculated)
        ]
        return features
    
    def _generate_recommendations(self, input_data: Dict[str, Any], will_change: bool) -> List[str]:
        """Generate clinical recommendations based on dry weight prediction"""
        recommendations = []
        
        # Main prediction recommendation
        if will_change:
            recommendations.append("⚠️ Dry weight adjustment predicted for next session")
            recommendations.append("Monitor fluid status closely and reassess dry weight")
        else:
            recommendations.append("✅ Current dry weight appears stable")
            recommendations.append("Continue with current dry weight target")
        
        # Clinical parameter recommendations
        if input_data['sys'] > 140:
            recommendations.append("High systolic BP detected - consider antihypertensive adjustment")
        
        if input_data['weight_gain'] > 3.0:
            recommendations.append("Excessive interdialytic weight gain - patient education needed")
        elif input_data['weight_gain'] < 1.0:
            recommendations.append("Low weight gain - monitor for signs of volume depletion")
        
        # UFR recommendations
        ufr = input_data['puf'] / (input_data['hd_duration'] * input_data['pre_hd_weight']) if (input_data['hd_duration'] * input_data['pre_hd_weight']) > 0 else 0
        if ufr > 13:
            recommendations.append("High UFR detected - risk of hypotension and cramping")
        elif ufr < 10:
            recommendations.append("Low UFR - consider longer treatment time if volume overloaded")
        
        # TMP recommendations
        if input_data['tmp'] > 200:
            recommendations.append("High transmembrane pressure - check for access issues")
        
        # Blood flow recommendations
        if input_data['bfr'] < 300:
            recommendations.append("Low blood flow rate - consider access evaluation")
        
        return recommendations


class URRPredictor:
    """
    URR (Urea Reduction Ratio) prediction service using LightGBM
    """
    
    def __init__(self, model_manager: MLModelManager):
        self.model_manager = model_manager
        self.model_name = 'urr'
        
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if URR will go to risk region next month using LightGBM model
        """
        try:
            # Load model
            model = self.model_manager.load_model(self.model_name)
            
            # Prepare features
            features = self._prepare_features(input_data)

            print(features)
            
            # Convert features to DataFrame for LightGBM compatibility
            import pandas as pd
            feature_names = [
                'Albumin (g/L)', 'Hb (g/dL)', 'S Ca (mmol/L)',
                'Serum Na Pre-HD (mmol/L)', 'URR', 'URR_diff', 
                'K_Diff', 'BU_Diff', 'SCR_Diff'
            ]
            X = pd.DataFrame([features], columns=feature_names)
            
            # Make classification prediction
            prediction = model.predict([features])[0]
            
            # Get prediction probabilities
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)[0]
                confidence = max(probabilities)
                risk_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                raise ValueError(f"Model {self.model_name} does not support probability predictions")
            
            # Interpret prediction
            at_risk = bool(prediction)
            risk_status = "At Risk" if at_risk else "Safe"
            adequacy_status = "Predicted Inadequate" if at_risk else "Predicted Adequate"
            
            # Generate URR-specific recommendations
            recommendations = self._generate_recommendations(input_data, at_risk)
            
            return {
                'patient_id': input_data.get('patient_id'),
                'urr_risk_predicted': at_risk,
                'risk_status': risk_status,
                'adequacy_status': adequacy_status,
                'current_urr': float(input_data['urr']),
                'target_urr_range': {'min': 65.0, 'max': 100.0},
                'risk_probability': round(float(risk_probability), 3),
                'confidence_score': round(float(confidence), 3),
                'recommendations': recommendations,
                'model_version': self.model_manager.get_model_version(self.model_name),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in URR prediction: {str(e)}")
            raise
    
    def _prepare_features(self, input_data: Dict[str, Any]) -> List[float]:
        """Prepare features for the LightGBM URR model"""
        # New feature order based on updated model training:
        # ['Albumin (g/L)', 'Hb (g/dL)', 'S Ca (mmol/L)', 'Serum Na Pre-HD (mmol/L)', 
        #  'URR', 'URR_diff', 'K_Diff', 'BU_Diff', 'SCR_Diff']
        
        # Calculate derived features
        k_diff = input_data['serum_k_pre_hd'] - input_data['serum_k_post_hd']
        bu_diff = input_data['bu_pre_hd'] - input_data['bu_post_hd']
        scr_diff = input_data['scr_pre_hd'] - input_data['scr_post_hd']
        
        features = [
            input_data['albumin'],                  # Albumin (g/L)
            input_data['hb'],                      # Hb (g/dL)
            input_data['s_ca'],                    # S Ca (mmol/L)
            input_data['serum_na_pre_hd'],         # Serum Na Pre-HD (mmol/L)
            input_data['urr'],                     # URR
            input_data['urr_diff'],                # URR_diff
            k_diff,                                # K_Diff (calculated)
            bu_diff,                               # BU_Diff (calculated)
            scr_diff                               # SCR_Diff (calculated)
        ]
        return features
    
    def _generate_recommendations(self, input_data: Dict[str, Any], at_risk: bool) -> List[str]:
        """Generate clinical recommendations based on URR risk prediction"""
        recommendations = []
        current_urr = input_data['urr']
        
        # URR-specific recommendations
        if at_risk:
            recommendations.append("⚠️ Patient predicted to have inadequate URR next month")
            if current_urr < 65:
                recommendations.append("Current URR below target - dialysis inadequacy detected")
                recommendations.append("Consider increasing treatment time or frequency")
                recommendations.append("Evaluate vascular access function")
            else:
                recommendations.append("Monitor closely - risk of URR decline detected")
                recommendations.append("Review dialysis prescription parameters")
        else:
            recommendations.append("✅ URR levels predicted to remain adequate")
            recommendations.append("Continue current dialysis regimen")
        
        # Lab-based recommendations for URR optimization
        if input_data['albumin'] < 35:
            recommendations.append("Low albumin may affect dialysis efficiency - nutritional support needed")
        
        if input_data['hb'] < 10:
            recommendations.append("Low hemoglobin - may impact dialysis tolerance and adequacy")
        
        # Access-related recommendations based on calculated differences
        bu_diff = input_data['bu_pre_hd'] - input_data['bu_post_hd']
        bu_reduction = (bu_diff / input_data['bu_pre_hd']) * 100 if input_data['bu_pre_hd'] > 0 else 0
        
        if bu_reduction < 65:
            recommendations.append("Inadequate urea reduction - check access flow and dialyzer function")
        
        # Electrolyte balance recommendations
        if input_data['serum_k_pre_hd'] > 5.5:
            recommendations.append("High potassium - dietary counseling and dialysate adjustment needed")
        
        if input_data['s_ca'] < 2.1:
            recommendations.append("Low calcium - consider calcium supplementation")
        elif input_data['s_ca'] > 2.6:
            recommendations.append("High calcium - review phosphate binders and vitamin D therapy")
        
        return recommendations


class HbPredictor:
    """
    Hemoglobin prediction service
    """
    
    def __init__(self, model_manager: MLModelManager):
        self.model_manager = model_manager
        self.model_name = 'hb'
        
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if Hb will go to risk region next month using ensemble model
        """
        try:
            # Load model bundle
            model_bundle = self.model_manager.load_model(self.model_name)
            
            # Prepare features
            features = self._prepare_features(input_data)
            
            # Only use ensemble model - throw error if not available
            if not isinstance(model_bundle, dict) or 'xgb' not in model_bundle:
                raise ValueError(f"Ensemble model required for {self.model_name}. Expected dict with 'xgb', 'lgbm', 'weights', 'threshold' keys.")
            
            # Validate ensemble components
            required_keys = ['xgb', 'lgbm', 'weights', 'threshold']
            missing_keys = [key for key in required_keys if key not in model_bundle]
            if missing_keys:
                raise ValueError(f"Missing ensemble components: {missing_keys}. Ensemble model must contain: {required_keys}")
            
            # Extract ensemble components
            xgb_model = model_bundle["xgb"]
            lgbm_model = model_bundle["lgbm"]
            w1, w2 = model_bundle["weights"]
            threshold = model_bundle["threshold"]
            
            # Validate models have predict_proba method
            if not hasattr(xgb_model, 'predict_proba'):
                raise ValueError("XGB model in ensemble does not support predict_proba")
            if not hasattr(lgbm_model, 'predict_proba'):
                raise ValueError("LGBM model in ensemble does not support predict_proba")
            
            # Convert features to DataFrame for compatibility
            import pandas as pd
            feature_names = model_bundle.get("features", [f"feature_{i}" for i in range(len(features))])
            X = pd.DataFrame([features], columns=feature_names)
            
            # Make ensemble prediction 
            xgb_probs = xgb_model.predict_proba(X)[:, 1]
            lgbm_probs = lgbm_model.predict_proba(X)[:, 1]
            probs_ensemble = w1 * xgb_probs + w2 * lgbm_probs
            prediction = (probs_ensemble >= threshold).astype(int)[0]
            
            # Set probabilities
            risk_probability = float(probs_ensemble[0])
            probabilities = [1 - risk_probability, risk_probability]
            confidence = max(probabilities)
            
            # Interpret prediction
            at_risk = bool(prediction)
            risk_status = "At Risk" if at_risk else "Safe"
            
            # Determine trend based on current Hb and risk prediction
            current_hb = input_data['hb']
            if at_risk:
                if current_hb < 10:
                    trend = "Declining to Critical"
                elif current_hb > 12:
                    trend = "Rising to Excessive"
                else:
                    trend = "Moving to Risk Zone"
            else:
                trend = "Stable in Target Range"
            
            # Generate recommendations
            recommendations = self._generate_recommendations(input_data, at_risk, current_hb)
            
            return {
                'hb_risk_predicted': at_risk,
                'risk_status': risk_status,
                'hb_trend': trend,
                'current_hb': float(current_hb),
                'target_hb_range': {'min': 10.0, 'max': 12.0},
                'risk_probability': round(float(risk_probability), 3),
                'recommendations': recommendations,
                'confidence_score': round(float(confidence), 3),
                'model_version': self.model_manager.get_model_version(self.model_name),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Hb prediction: {str(e)}")
            raise
    
    def _prepare_features(self, input_data: Dict[str, Any]) -> List[float]:
        """Prepare features for the model based on actual feature columns"""
        # New feature order based on updated model training:
        # ['Albumin (g/L)', 'S Ca (mmol/L)', 'Serum Na Pre-HD (mmol/L)', 'UA (mg/dL)', 
        #  'Hb_diff', 'Hb (g/dL)', 'Albumin_BU_Ratio', 'K_Diff', 'BU_Diff', 'SCR_Diff']
        
        # Calculate derived features
        albumin_bu_ratio = input_data['albumin'] / (input_data['bu_pre_hd']+1) if input_data['bu_pre_hd'] != 0 else 0
        k_diff = input_data['serum_k_pre_hd'] - input_data['serum_k_post_hd']
        bu_diff = input_data['bu_pre_hd'] - input_data['bu_post_hd']
        scr_diff = input_data['scr_pre_hd'] - input_data['scr_post_hd']
        
        features = [
            input_data['albumin'],                  # Albumin (g/L)
            input_data['s_ca'],                    # S Ca (mmol/L)
            input_data['serum_na_pre_hd'],         # Serum Na Pre-HD (mmol/L)
            input_data['ua'],                      # UA (mg/dL)
            input_data['hb_diff'],                 # Hb_diff
            input_data['hb'],                      # Hb (g/dL)
            albumin_bu_ratio,                      # Albumin_BU_Ratio (calculated)
            k_diff,                                # K_Diff (calculated)
            bu_diff,                               # BU_Diff (calculated)
            scr_diff                               # SCR_Diff (calculated)
        ]
        return features
    
    def _generate_recommendations(self, input_data: Dict[str, Any], at_risk: bool, current_hb: float) -> List[str]:
        """Generate clinical recommendations based on risk prediction and lab values"""
        recommendations = []
        
        # Risk-based recommendations
        if at_risk:
            recommendations.append("⚠️ Patient predicted to enter Hb risk zone next month")
            if current_hb < 10:
                recommendations.append("Current Hb below target - urgent intervention needed")
                recommendations.append("Consider increasing EPO dose or iron supplementation")
            elif current_hb > 12:
                recommendations.append("Current Hb above target - risk of cardiovascular complications")
                recommendations.append("Consider reducing EPO dose and monitor closely")
            else:
                recommendations.append("Monitor closely and consider preventive measures")
        else:
            recommendations.append("✅ Hb levels predicted to remain stable")
            recommendations.append("Continue current treatment regimen")
        
        # Lab-based recommendations
        if input_data['albumin'] < 35:
            recommendations.append("Low albumin - nutritional counseling recommended")
        
        if input_data['s_ca'] < 2.1:
            recommendations.append("Low calcium - consider calcium supplementation")
        elif input_data['s_ca'] > 2.6:
            recommendations.append("High calcium - review phosphate binders")
        
        if input_data['serum_k_pre_hd'] > 5.5:
            recommendations.append("High potassium - dietary restriction advised")
        elif input_data['serum_k_pre_hd'] < 3.5:
            recommendations.append("Low potassium - monitor for arrhythmias")
        
        # Dialysis adequacy
        bu_reduction = ((input_data['bu_pre_hd'] - input_data['bu_post_hd']) / input_data['bu_pre_hd']) * 100
        if bu_reduction < 65:
            recommendations.append("Inadequate dialysis - consider increasing treatment time/frequency")
        
        return recommendations


# Global model manager instance
model_manager = MLModelManager()

# Global predictor instances
dry_weight_predictor = DryWeightPredictor(model_manager)
urr_predictor = URRPredictor(model_manager)
hb_predictor = HbPredictor(model_manager)
