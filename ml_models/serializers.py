from rest_framework import serializers


class DryWeightPredictionSerializer(serializers.Serializer):
    """
    Serializer for dry weight prediction input data using LightGBM model
    Based on dialysis session parameters with 19 features
    """
    # Patient identifier
    patient_id = serializers.CharField(max_length=50, help_text="Patient identifier")
    
    # Original features from dialysis session data
    ap = serializers.FloatField(min_value=-500, max_value=0, help_text="AP (mmHg)")
    auf = serializers.FloatField(min_value=0, max_value=10000, help_text="AUF (ml)")
    bfr = serializers.FloatField(min_value=100, max_value=500, help_text="BFR (ml/min)")
    hd_duration = serializers.FloatField(min_value=1, max_value=8, help_text="HD duration (h)")
    puf = serializers.FloatField(min_value=0, max_value=10000, help_text="PUF (ml)")
    tmp = serializers.FloatField(min_value=0, max_value=500, help_text="TMP (mmHg)")
    vp = serializers.FloatField(min_value=0, max_value=500, help_text="VP (mmHg)")
    weight_gain = serializers.FloatField(min_value=0, max_value=10, help_text="Weight gain (kg)")
    sys = serializers.FloatField(min_value=60, max_value=250, help_text="SYS (mmHg)")
    dia = serializers.FloatField(min_value=40, max_value=150, help_text="DIA (mmHg)")
    pre_hd_weight = serializers.FloatField(min_value=20, max_value=300, help_text="Pre HD weight (kg)")
    post_hd_weight = serializers.FloatField(min_value=20, max_value=300, help_text="Post HD weight (kg)")
    dry_weight = serializers.FloatField(min_value=20, max_value=300, help_text="Dry weight (kg)")
    
    # Optional rolling averages (will use current session values if not provided)
    weight_gain_avg_3 = serializers.FloatField(required=False, min_value=0, max_value=10, 
                                               help_text="3-session rolling average of Weight gain (kg)")
    sys_avg_3 = serializers.FloatField(required=False, min_value=60, max_value=250, 
                                       help_text="3-session rolling average of SYS (mmHg)")


class DryWeightPredictionResponseSerializer(serializers.Serializer):
    """
    Serializer for dry weight change prediction response
    """
    patient_id = serializers.CharField()
    dry_weight_change_predicted = serializers.BooleanField()
    prediction_status = serializers.CharField()  # "Change Expected" or "Stable"
    change_probability = serializers.FloatField()
    confidence_score = serializers.FloatField()
    current_dry_weight = serializers.FloatField()
    current_weight_gain = serializers.FloatField()
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Clinical recommendations based on dry weight prediction"
    )
    model_version = serializers.CharField()
    prediction_date = serializers.DateTimeField()


class URRPredictionSerializer(serializers.Serializer):
    """
    Serializer for URR (Urea Reduction Ratio) prediction input data using LightGBM model
    Features: ['Albumin (g/L)', 'Hb (g/dL)', 'S Ca (mmol/L)', 'Serum Na Pre-HD (mmol/L)', 
              'URR', 'URR_diff', 'K_Diff', 'BU_Diff', 'SCR_Diff']
    """
    # Laboratory parameters
    albumin = serializers.FloatField(min_value=10, max_value=60, help_text="Albumin (g/L)")
    hb = serializers.FloatField(min_value=2, max_value=20, help_text="Hemoglobin (g/dL)")
    s_ca = serializers.FloatField(min_value=1.5, max_value=10, help_text="S Ca (mmol/L)")
    serum_na_pre_hd = serializers.FloatField(min_value=120, max_value=150, help_text="Serum Na Pre-HD (mmol/L)")
    
    # URR parameters
    urr = serializers.FloatField(min_value=30, max_value=95, help_text="Current URR (%)")
    urr_diff = serializers.FloatField(min_value=-30, max_value=30, help_text="URR difference from previous session (%)")
    
    # Dialysis efficiency parameters (for calculating differences)
    serum_k_pre_hd = serializers.FloatField(min_value=2.0, max_value=8.0, help_text="Serum K Pre-HD (mmol/L)")
    serum_k_post_hd = serializers.FloatField(min_value=2.0, max_value=7.0, help_text="Serum K Post-HD (mmol/L)")
    bu_pre_hd = serializers.FloatField(min_value=10, max_value=100, help_text="BU - pre HD (mmol/L)")
    bu_post_hd = serializers.FloatField(min_value=5, max_value=50, help_text="BU - post HD (mmol/L)")
    scr_pre_hd = serializers.FloatField(min_value=10, max_value=2000, help_text="SCR- pre HD (µmol/L)")
    scr_post_hd = serializers.FloatField(min_value=10, max_value=1500, help_text="SCR- post HD (µmol/L)")
    
    # Optional patient ID
    patient_id = serializers.CharField(max_length=50, required=False, help_text="Patient identifier")


class URRPredictionResponseSerializer(serializers.Serializer):
    """
    Serializer for URR risk prediction response
    """
    patient_id = serializers.CharField(required=False)
    urr_risk_predicted = serializers.BooleanField()
    risk_status = serializers.CharField()  # "At Risk" or "Safe"
    adequacy_status = serializers.CharField()  # "Predicted Adequate" or "Predicted Inadequate"
    current_urr = serializers.FloatField()
    target_urr_range = serializers.DictField()  # {min: 65.0, max: 100.0}
    risk_probability = serializers.FloatField()
    confidence_score = serializers.FloatField()
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Clinical recommendations based on URR risk prediction"
    )
    model_version = serializers.CharField()
    prediction_date = serializers.DateTimeField()


class HbPredictionSerializer(serializers.Serializer):
    """
    Serializer for Hemoglobin (Hb) prediction input data
    Based on the actual model features
    """
    # Laboratory parameters
    albumin = serializers.FloatField(min_value=10, max_value=60, help_text="Albumin (g/L)")
    bu_post_hd = serializers.FloatField(min_value=5, max_value=50, help_text="BU - post HD (mmol/L)")
    bu_pre_hd = serializers.FloatField(min_value=10, max_value=100, help_text="BU - pre HD (mmol/L)")
    s_ca = serializers.FloatField(min_value=1.5, max_value=10, help_text="S Ca (mmol/L)")
    scr_post_hd = serializers.FloatField(min_value=10, max_value=1500, help_text="SCR- post HD (µmol/L)")
    scr_pre_hd = serializers.FloatField(min_value=10, max_value=2000, help_text="SCR- pre HD (µmol/L)")
    serum_k_post_hd = serializers.FloatField(min_value=0, max_value=7.0, help_text="Serum K Post-HD (mmol/L)")
    serum_k_pre_hd = serializers.FloatField(min_value=0, max_value=8.0, help_text="Serum K Pre-HD (mmol/L)")
    serum_na_pre_hd = serializers.FloatField(min_value=0, max_value=150, help_text="Serum Na Pre-HD (mmol/L)")
    ua = serializers.FloatField(min_value=0, max_value=1000, help_text="UA (micro mol/L)")#check units for UA
    hb_diff = serializers.FloatField(min_value=-7.0, max_value=7.0, help_text="Hb_diff (g/dL)")
    hb = serializers.FloatField(min_value=2, max_value=20, help_text="Current Hb (g/dL)")


class HbPredictionResponseSerializer(serializers.Serializer):
    """
    Serializer for Hb risk prediction response
    """
    hb_risk_predicted = serializers.BooleanField()
    risk_status = serializers.CharField()  # "At Risk" or "Safe"
    hb_trend = serializers.CharField()  # Risk-based trend description
    current_hb = serializers.FloatField()
    target_hb_range = serializers.DictField()  # {min: 10, max: 12}
    risk_probability = serializers.FloatField()
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Clinical recommendations based on risk prediction"
    )
    confidence_score = serializers.FloatField()
    model_version = serializers.CharField()
    prediction_date = serializers.DateTimeField()


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for error responses
    """
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
