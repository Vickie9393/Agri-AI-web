"""
╔══════════════════════════════════════════════════════════════════╗
║  AgriAI — Database Models                                        ║
║  Models: OTP, UserProfile, CropPlan, DiseaseRecord,             ║
║          PestControl, FertilizerLog, WeatherLog,                 ║
║          DiseaseDataset, MLModelInfo, ChatHistory, Contact       ║
╚══════════════════════════════════════════════════════════════════╝
"""
import random, string
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ══════════════════════════════════════
# OTP MODEL
# ══════════════════════════════════════
class OTP(models.Model):
    TYPE_CHOICES    = [('email', 'Email'), ('mobile', 'Mobile')]
    PURPOSE_CHOICES = [('register', 'Registration'), ('login', 'Login'), ('reset', 'Password Reset')]

    identifier = models.CharField(max_length=255)
    otp_code   = models.CharField(max_length=6)
    otp_type   = models.CharField(max_length=10, choices=TYPE_CHOICES, default='email')
    purpose    = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='login')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)
    attempts   = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP'

    def is_valid(self):
        from django.conf import settings
        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        max_att = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return (not self.is_used) and (self.attempts < max_att) and (elapsed < expiry * 60)

    @staticmethod
    def generate():
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"OTP({self.identifier}) [{self.purpose}]"


# ══════════════════════════════════════
# USER PROFILE
# ══════════════════════════════════════
class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile      = models.CharField(max_length=15, blank=True)
    location    = models.CharField(max_length=255, blank=True)
    farm_size   = models.FloatField(null=True, blank=True, help_text='Acres')
    avatar      = models.ImageField(upload_to='avatars/', blank=True)
    is_verified = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


# ══════════════════════════════════════
# CROP PLAN
# ══════════════════════════════════════
class CropPlan(models.Model):
    SEASON_CHOICES = [
        ('kharif','Kharif'), ('rabi','Rabi'), ('zaid','Zaid'), ('perennial','Perennial')
    ]
    STATUS_CHOICES = [
        ('planned','Planned'), ('growing','Growing'),
        ('harvested','Harvested'), ('failed','Failed')
    ]
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crop_plans')
    crop_name         = models.CharField(max_length=100)
    variety           = models.CharField(max_length=100, blank=True)
    season            = models.CharField(max_length=20, choices=SEASON_CHOICES)
    field_area        = models.FloatField()
    sowing_date       = models.DateField()
    expected_harvest  = models.DateField()
    soil_type         = models.CharField(max_length=100, blank=True)
    irrigation_method = models.CharField(max_length=100, blank=True)
    notes             = models.TextField(blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    ai_recommendations= models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════
# DISEASE DATASET (CSV Upload + Training)
# ══════════════════════════════════════
class DiseaseDataset(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('training', 'Training'),
        ('trained',  'Trained'),
        ('failed',   'Failed'),
    ]
    uploaded_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    name          = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    csv_file      = models.FileField(upload_to='datasets/')
    total_rows    = models.IntegerField(default=0)
    unique_labels = models.IntegerField(default=0)
    label_names   = models.JSONField(default=list)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    accuracy      = models.FloatField(null=True, blank=True)
    training_log  = models.TextField(blank=True)
    model_path    = models.CharField(max_length=500, blank=True)
    uploaded_at   = models.DateTimeField(auto_now_add=True)
    trained_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} [{self.status}]"


# ══════════════════════════════════════
# DISEASE RECOGNITION RECORD
# ══════════════════════════════════════
class DiseaseRecord(models.Model):
    user                    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disease_records')
    crop_name               = models.CharField(max_length=100)
    image                   = models.ImageField(upload_to='disease_images/')
    detected_disease        = models.CharField(max_length=255, blank=True)
    confidence_score        = models.FloatField(null=True, blank=True)
    severity                = models.CharField(max_length=50, blank=True)
    treatment_recommendation= models.TextField(blank=True)
    all_predictions         = models.JSONField(default=list)   # Top 3 predictions
    model_used              = models.CharField(max_length=100, default='rule_based')
    analyzed_at             = models.DateTimeField(null=True, blank=True)
    created_at              = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════
# PEST CONTROL
# ══════════════════════════════════════
class PestControlRecord(models.Model):
    SEV = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]
    user                 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pest_records')
    crop_name            = models.CharField(max_length=100)
    pest_name            = models.CharField(max_length=100)
    severity             = models.CharField(max_length=20, choices=SEV)
    affected_area        = models.FloatField(default=1)
    symptoms             = models.TextField()
    recommended_pesticide= models.CharField(max_length=200, blank=True)
    dosage               = models.CharField(max_length=100, blank=True)
    application_method   = models.CharField(max_length=200, blank=True)
    organic_alternative  = models.TextField(blank=True)
    ai_recommendation    = models.TextField(blank=True)
    reported_date        = models.DateField(auto_now_add=True)
    resolved             = models.BooleanField(default=False)

    class Meta:
        ordering = ['-reported_date']


# ══════════════════════════════════════
# FERTILIZER LOG
# ══════════════════════════════════════
class FertilizerLog(models.Model):
    user                 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fertilizer_logs')
    crop_name            = models.CharField(max_length=100)
    field_area           = models.FloatField()
    soil_type            = models.CharField(max_length=100)
    crop_stage           = models.CharField(max_length=100)
    nitrogen_kg          = models.FloatField(default=0)
    phosphorus_kg        = models.FloatField(default=0)
    potassium_kg         = models.FloatField(default=0)
    recommended_fertilizer= models.TextField(blank=True)
    application_schedule = models.TextField(blank=True)
    estimated_cost       = models.FloatField(null=True, blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════
# WEATHER LOG
# ══════════════════════════════════════
class WeatherLog(models.Model):
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_logs')
    location          = models.CharField(max_length=255)
    latitude          = models.FloatField(null=True, blank=True)
    longitude         = models.FloatField(null=True, blank=True)
    temperature       = models.FloatField()
    humidity          = models.FloatField()
    wind_speed        = models.FloatField()
    weather_condition = models.CharField(max_length=100)
    forecast_data     = models.JSONField(default=dict)
    farming_advisory  = models.TextField(blank=True)
    fetched_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fetched_at']


# ══════════════════════════════════════
# CHATBOT HISTORY
# ══════════════════════════════════════
class ChatHistory(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    session_id      = models.CharField(max_length=100)
    role            = models.CharField(max_length=20)   # 'user' | 'assistant'
    message         = models.TextField()
    feature_context = models.CharField(max_length=50, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


# ══════════════════════════════════════
# CONTACT INQUIRY
# ══════════════════════════════════════
class ContactInquiry(models.Model):
    name         = models.CharField(max_length=100)
    email        = models.EmailField()
    subject      = models.CharField(max_length=200)
    message      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved  = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name_plural = 'Contact Inquiries'
