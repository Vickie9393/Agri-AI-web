"""
╔══════════════════════════════════════════════════════════════════╗
║  AgriAI URL Configuration                                        ║
║  All routes with descriptions                                    ║
╚══════════════════════════════════════════════════════════════════╝
"""
from django.urls import path
from . import views

urlpatterns = [

    # ── Pages ────────────────────────────────────────────
    path('',              views.home_view,       name='home'),
    path('logout/',       views.logout_view,     name='logout'),
    path('dashboard/',    views.dashboard_view,  name='dashboard'),
    path('crop-planner/', views.crop_planner_view, name='crop_planner'),
    path('disease/',      views.disease_view,    name='disease'),
    path('pest-control/', views.pest_view,       name='pest_control'),
    path('fertilizer/',   views.fertilizer_view, name='fertilizer'),
    path('weather/',      views.weather_view,    name='weather'),
    path('profile/',      views.profile_view,    name='profile'),

    # ── AUTH APIs ─────────────────────────────────────────
    path('api/auth/send-otp/',        views.api_send_otp,        name='api_send_otp'),
    path('api/auth/verify-register/', views.api_verify_register, name='api_verify_register'),
    path('api/auth/verify-login/',    views.api_verify_login,    name='api_verify_login'),
    path('api/auth/google/',          views.api_google_login,    name='api_google_login'),
    path('api/auth/missed-call-webhook/', views.api_missed_call_webhook, name='api_missed_call_webhook'),

    # ── CROP APIs ─────────────────────────────────────────
    path('api/crop/add/',            views.api_crop_add,    name='api_crop_add'),
    path('api/crop/delete/<int:pk>/',views.api_crop_delete, name='api_crop_delete'),
    path('api/crop/list/',           views.api_crop_list,   name='api_crop_list'),

    # ── DISEASE APIs ──────────────────────────────────────
    path('api/disease/analyze/',        views.api_disease_analyze,        name='api_disease_analyze'),
    path('api/disease/upload-dataset/', views.api_disease_upload_dataset, name='api_disease_upload_dataset'),
    path('api/disease/train/',          views.api_disease_train,          name='api_disease_train'),
    path('api/disease/model-status/',   views.api_model_status,           name='api_model_status'),
    path('api/disease/dataset-list/',   views.api_dataset_list,           name='api_dataset_list'),
    path('api/disease/auto-setup/',     views.api_disease_auto_setup,     name='api_disease_auto_setup'),

    # ── PEST APIs ─────────────────────────────────────────
    path('api/pest/add/',              views.api_pest_add,     name='api_pest_add'),
    path('api/pest/resolve/<int:pk>/', views.api_pest_resolve, name='api_pest_resolve'),

    # ── FERTILIZER APIs ───────────────────────────────────
    path('api/fertilizer/calculate/', views.api_fertilizer_calc, name='api_fertilizer_calc'),

    # ── WEATHER API ───────────────────────────────────────
    path('api/weather/', views.api_weather, name='api_weather'),

    # ── CHATBOT API ───────────────────────────────────────
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),

    # ── CONTACT API ───────────────────────────────────────
    path('api/contact/', views.api_contact, name='api_contact'),
]
