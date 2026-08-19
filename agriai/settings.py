"""
╔══════════════════════════════════════════════════════════════════╗
║           AgriAI — Django Settings                               ║
║  🔑 ALL API KEYS ARE MARKED WITH  ← SET THIS                    ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────
# 🔑 SECURITY KEY — Change this in production!
# ─────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'agriai-dev-secret-key-change-in-production-2025'   # ← SET THIS in production
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']   # ← Restrict to your domain in production
CSRF_TRUSTED_ORIGINS = ['https://agri-ai-web.onrender.com', 'https://*.onrender.com']

# ─────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'agriai_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',       # Static files in prod
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agriai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agriai.wsgi.application'

# ─────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # ── For PostgreSQL in production: ──────────────────────────
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': os.environ.get('DB_NAME', 'agriai_db'),         # ← SET THIS
        # 'USER': os.environ.get('DB_USER', 'postgres'),          # ← SET THIS
        # 'PASSWORD': os.environ.get('DB_PASSWORD', ''),          # ← SET THIS
        # 'HOST': os.environ.get('DB_HOST', 'localhost'),
        # 'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ─────────────────────────────────────────────────────────────────
# 🔑 EMAIL SETTINGS (for OTP via email)
# ─────────────────────────────────────────────────────────────────
# HOW TO GET: Gmail → Account → Security → App Passwords → Generate
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST      = 'smtp.gmail.com'
EMAIL_PORT      = 587
EMAIL_USE_TLS   = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER',     'shivamshah3111@gmail.com')   # ← SET THIS
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'vvgtmqwriafacjhs')      # ← SET THIS
DEFAULT_FROM_EMAIL  = EMAIL_HOST_USER

# ─────────────────────────────────────────────────────────────────
# 🔑 TWILIO SETTINGS (for OTP via SMS)
# ─────────────────────────────────────────────────────────────────
# HOW TO GET: Sign up at https://www.twilio.com → Console → Account Info
TWILIO_ACCOUNT_SID  = os.environ.get('TWILIO_ACCOUNT_SID', 'AC204272b3c2e81bc40b09740bc4bd22c7')  # ← SET THIS
TWILIO_AUTH_TOKEN   = os.environ.get('TWILIO_AUTH_TOKEN', '61accee02e88d598384f89da3e90f90e')       # ← SET THIS
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+17372212163')                      # ← SET THIS

# ─────────────────────────────────────────────────────────────────
# 🔑 GOOGLE OAUTH SETTINGS (for Google Sign-In)
# ─────────────────────────────────────────────────────────────────
# HOW TO GET: Google Cloud Console → APIs & Services → Credentials → OAuth Client ID
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '567408831528-1qma1s9jeb6hhgaqfpqkag77p5prfj5a.apps.googleusercontent.com') # ← SET THIS

# ─────────────────────────────────────────────────────────────────
# 🔑 OPENWEATHERMAP API (for Weather Forecast)
# ─────────────────────────────────────────────────────────────────
# HOW TO GET: Sign up at https://openweathermap.org/api → API Keys tab
# Free tier: 1000 calls/day — sufficient for most use
OPENWEATHER_API_KEY = 'ec0ba26ebcae2c0f36c5309b729a80d0'   # ← SET THIS
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# ─────────────────────────────────────────────────────────────────
# OTP CONFIG
# ─────────────────────────────────────────────────────────────────
OTP_EXPIRY_MINUTES = 10          # OTP expires after 10 minutes
OTP_MAX_ATTEMPTS   = 3           # Lock after 3 wrong attempts

# ─────────────────────────────────────────────────────────────────
# STATIC & MEDIA FILES
# ─────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N = True
USE_TZ   = True

STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────────────────────────
SESSION_COOKIE_AGE    = 86400   # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# ─────────────────────────────────────────────────────────────────
# CORS (allow frontend JS calls)
# ─────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # ← Restrict to your domain in production

# ─────────────────────────────────────────────────────────────────
# ML MODEL PATHS
# ─────────────────────────────────────────────────────────────────
ML_MODELS_DIR   = BASE_DIR / 'media' / 'models'
ML_DATASETS_DIR = BASE_DIR / 'media' / 'datasets'
DISEASE_MODEL_PATH = BASE_DIR / 'agriai_app' / 'ml' / 'cnn_disease_model.keras'
LABEL_ENCODER_PATH = BASE_DIR / 'agriai_app' / 'ml' / 'cnn_classes.json'

# ─────────────────────────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800   # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800   # 50 MB

# Auth redirects
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
