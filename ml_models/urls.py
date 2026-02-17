from django.urls import path
from . import views

urlpatterns = [
    # Health check and info endpoints
    path('health/', views.health_check, name='ml_health_check'),
    path('models/', views.models_info, name='models_info'),
    
    # Prediction endpoints
    path('predict/dry-weight/', views.predict_dry_weight, name='predict_dry_weight'),
    path('predict/urr/', views.predict_urr, name='predict_urr'),
    path('predict/hb/', views.predict_hb, name='predict_hb'),
]
