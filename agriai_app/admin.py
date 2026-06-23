from django.contrib import admin
from .models import (OTP, UserProfile, CropPlan, DiseaseRecord, DiseaseDataset,
                     PestControlRecord, FertilizerLog, WeatherLog, ChatHistory, ContactInquiry)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['identifier','otp_code','otp_type','purpose','is_used','attempts','created_at']
    list_filter  = ['otp_type','purpose','is_used']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user','mobile','location','is_verified','created_at']

@admin.register(CropPlan)
class CropPlanAdmin(admin.ModelAdmin):
    list_display = ['crop_name','user','season','field_area','status','sowing_date']
    list_filter  = ['season','status']

@admin.register(DiseaseDataset)
class DiseaseDatasetAdmin(admin.ModelAdmin):
    list_display = ['name','uploaded_by','total_rows','unique_labels','status','accuracy','uploaded_at']
    list_filter  = ['status']
    readonly_fields = ['training_log']

@admin.register(DiseaseRecord)
class DiseaseRecordAdmin(admin.ModelAdmin):
    list_display = ['crop_name','user','detected_disease','confidence_score','severity','model_used','created_at']

@admin.register(PestControlRecord)
class PestAdmin(admin.ModelAdmin):
    list_display = ['pest_name','crop_name','user','severity','resolved','reported_date']
    list_filter  = ['severity','resolved']

@admin.register(FertilizerLog)
class FertilizerAdmin(admin.ModelAdmin):
    list_display = ['crop_name','user','field_area','nitrogen_kg','phosphorus_kg','potassium_kg','estimated_cost','created_at']

@admin.register(WeatherLog)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ['location','user','temperature','humidity','weather_condition','fetched_at']

@admin.register(ContactInquiry)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name','email','subject','is_resolved','submitted_at']
    list_filter  = ['is_resolved']
