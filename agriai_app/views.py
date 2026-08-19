"""
╔══════════════════════════════════════════════════════════════════════════╗
║  AgriAI — All Views & API Endpoints                                      ║
║                                                                          ║
║  🌐 API ENDPOINTS SUMMARY:                                               ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  AUTH:                                                                   ║
║    POST /api/auth/send-otp/           → Send OTP (email/SMS)            ║
║    POST /api/auth/verify-login/       → Verify OTP + Login              ║
║    POST /api/auth/verify-register/    → Verify OTP + Register           ║
║    GET  /logout/                      → Logout                          ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  CROP PLANNER:                                                           ║
║    POST /api/crop/add/                → Add new crop plan               ║
║    POST /api/crop/update/<id>/        → Update crop plan                ║
║    GET  /api/crop/delete/<id>/        → Delete crop plan                ║
║    GET  /api/crop/list/               → List all crop plans (JSON)      ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  DISEASE RECOGNITION:                                                    ║
║    POST /api/disease/analyze/         → Upload image → AI diagnosis     ║
║    POST /api/disease/upload-dataset/  → Upload CSV training dataset     ║
║    POST /api/disease/train/           → Train model from dataset        ║
║    GET  /api/disease/model-status/    → Check trained model status      ║
║    GET  /api/disease/dataset-list/    → List all uploaded datasets      ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  PEST CONTROL:                                                           ║
║    POST /api/pest/add/                → Log pest + get recommendation   ║
║    POST /api/pest/resolve/<id>/       → Mark pest as resolved           ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  FERTILIZER:                                                             ║
║    POST /api/fertilizer/calculate/    → Calculate NPK + cost            ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  WEATHER:                                                                ║
║    POST /api/weather/                 → Fetch weather + advisory        ║
║         🔑 Requires: OPENWEATHER_API_KEY in settings.py                 ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  CHATBOT:                                                                ║
║    POST /api/chatbot/                 → Chat message (supports images)  ║
║  ─────────────────────────────────────────────────────────────────────── ║
║  CONTACT:                                                                ║
║    POST /api/contact/                 → Submit contact inquiry          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json, uuid, threading, os
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    OTP, UserProfile, CropPlan, DiseaseRecord, DiseaseDataset,
    PestControlRecord, FertilizerLog, WeatherLog, ChatHistory, ContactInquiry
)


# ═══════════════════════════════════════════════════════════
# ██  HELPERS
# ═══════════════════════════════════════════════════════════

def json_response(data, status=200):
    return JsonResponse(data, status=status)

def err(msg, status=400):
    return JsonResponse({'success': False, 'error': msg}, status=status)

def ok(data=None, **kwargs):
    res = {'success': True}
    if data: res.update(data)
    res.update(kwargs)
    return JsonResponse(res)

def parse_body(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}

def get_csrf(request):
    """Utility: get CSRF from cookie"""
    return request.COOKIES.get('csrftoken', '')


# ─── Email OTP Sender ────────────────────────────────────────
def send_otp_email(email, otp_code, purpose):
    """
    🔑 Uses: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD in settings.py
    Setup: Gmail → Account → Security → App Passwords → Generate
    """
    try:
        send_mail(
            subject=f'AgriAI OTP — {purpose.title()}',
            message=(
                f'Dear AgriAI User,\n\n'
                f'Your One-Time Password (OTP) is:  {otp_code}\n\n'
                f'Valid for {settings.OTP_EXPIRY_MINUTES} minutes.\n'
                f'Do NOT share with anyone.\n\n'
                f'— AgriAI Team 🌿'
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return True, None
    except Exception as e:
        return False, str(e)


# ─── SMS OTP Sender ──────────────────────────────────────────
def send_otp_sms(mobile, otp_code):
    """
    🔑 Uses: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    Setup: https://www.twilio.com → Console → Account Info
    """
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f'AgriAI OTP: {otp_code}. Valid {settings.OTP_EXPIRY_MINUTES} mins. Do NOT share.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=mobile,
        )
        return True, None
    except ImportError:
        return False, 'Twilio not installed. Run: pip install twilio'
    except Exception as e:
        return False, str(e)


# ─── Farming Advisory ────────────────────────────────────────
def farming_advisory(temp, humidity, condition):
    tips = []
    cond = condition.lower()
    if temp > 38:   tips.append('🌡️ Extreme heat! Irrigate before 8 AM or after 6 PM.')
    elif temp > 32: tips.append('☀️ High temperature. Increase irrigation frequency.')
    elif temp < 10: tips.append('❄️ Cold alert! Protect sensitive crops from frost tonight.')
    if humidity > 85: tips.append('💧 High humidity — watch for fungal diseases. Spray Mancozeb preventively.')
    elif humidity < 25: tips.append('🏜️ Very dry conditions. Mulch crops and irrigate immediately.')
    if 'rain' in cond:   tips.append('🌧️ Rain expected — postpone pesticide/fertilizer application.')
    if 'storm' in cond:  tips.append('⛈️ Storm warning! Stake tall crops and secure equipment.')
    if 'fog'  in cond:   tips.append('🌫️ Foggy conditions — watch for early blight. Improve air flow.')
    if not tips: tips.append('✅ Weather is favorable for all farming activities today.')
    return ' '.join(tips)


# ═══════════════════════════════════════════════════════════
# ██  PAGE VIEWS (HTML renders)
# ═══════════════════════════════════════════════════════════

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'agriai/auth.html', {
        'google_client_id': settings.GOOGLE_OAUTH_CLIENT_ID
    })

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='/')
def dashboard_view(request):
    u = request.user
    return render(request, 'agriai/dashboard.html', {
        'crop_count':       CropPlan.objects.filter(user=u, status='growing').count(),
        'disease_count':    DiseaseRecord.objects.filter(user=u).count(),
        'pest_count':       PestControlRecord.objects.filter(user=u, resolved=False).count(),
        'fertilizer_count': FertilizerLog.objects.filter(user=u).count(),
        'recent_crops':     CropPlan.objects.filter(user=u)[:3],
        'recent_disease':   DiseaseRecord.objects.filter(user=u)[:3],
        'model_trained':    os.path.exists(str(settings.DISEASE_MODEL_PATH)),
    })

@login_required(login_url='/')
def crop_planner_view(request):
    crops = CropPlan.objects.filter(user=request.user)
    return render(request, 'agriai/crop_planner.html', {'crops': crops})

@login_required(login_url='/')
def disease_view(request):
    records  = DiseaseRecord.objects.filter(user=request.user)
    datasets = DiseaseDataset.objects.filter(uploaded_by=request.user)
    trained  = os.path.exists(str(settings.DISEASE_MODEL_PATH))
    return render(request, 'agriai/disease_recognition.html', {
        'records': records, 'datasets': datasets, 'model_trained': trained
    })

@login_required(login_url='/')
def pest_view(request):
    return render(request, 'agriai/pest_control.html', {
        'records': PestControlRecord.objects.filter(user=request.user)
    })

@login_required(login_url='/')
def fertilizer_view(request):
    return render(request, 'agriai/fertilizer.html', {
        'logs': FertilizerLog.objects.filter(user=request.user)
    })

@login_required(login_url='/')
def weather_view(request):
    return render(request, 'agriai/weather.html')

@login_required(login_url='/')
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        if first_name: user.first_name = first_name
        if last_name: user.last_name = last_name
        if username: user.username = username
        if email: user.email = email
        user.save()
        return redirect('dashboard')
        
    return render(request, 'agriai/profile.html')


# ═══════════════════════════════════════════════════════════
# ██  AUTH APIs
# ═══════════════════════════════════════════════════════════

@csrf_exempt
def api_send_otp(request):
    """
    ┌─────────────────────────────────────────────────────────┐
    │  POST /api/auth/send-otp/                               │
    │  Body: { identifier, type: "email"|"mobile", purpose } │
    │  🔑 Email:  needs EMAIL_HOST_USER + EMAIL_HOST_PASSWORD  │
    │  🔑 SMS:    needs TWILIO_* in settings.py               │
    └─────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    data       = parse_body(request)
    identifier = data.get('identifier', '').strip()
    otp_type   = data.get('type', 'email')
    purpose    = data.get('purpose', 'login')

    if not identifier:
        return err('Email or mobile number is required')

    # Invalidate old OTPs
    OTP.objects.filter(identifier=identifier, is_used=False).update(is_used=True)

    otp_code = OTP.generate()
    OTP.objects.create(identifier=identifier, otp_code=otp_code, otp_type=otp_type, purpose=purpose)

    if otp_type == 'email':
        success, error = send_otp_email(identifier, otp_code, purpose)
    else:
        success, error = send_otp_sms(identifier, otp_code)

    if success:
        return ok(message=f'OTP sent to your {otp_type}')
    else:
        # Demo mode: return OTP in response (REMOVE IN PRODUCTION)
        return ok(
            message=f'[DEMO] OTP is: {otp_code}  (Setup error: {error})', 
            demo_otp=otp_code,
            error_reason=error
        )

@csrf_exempt
def api_google_login(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/auth/google/                                       │
    │  Body: { credential } (Google JWT Token)                     │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)
    
    data = parse_body(request)
    token = data.get('credential')
    if not token:
        return err('Google credential missing')
    
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
        
        email = idinfo['email']
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        user = User.objects.filter(email=email).first()
        if not user:
            username = email.split('@')[0]
            base_username = username
            count = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{count}"
                count += 1
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(user=user, is_verified=True)
            
        login(request, user)
        return ok(message='Logged in with Google successfully', redirect='/dashboard/')
        
    except ValueError as e:
        return err(f'Invalid Google token: {str(e)}')
    except ImportError:
        return err('google-auth library not installed')

@csrf_exempt
def api_missed_call_webhook(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/auth/missed-call-webhook/                          │
    │  Webhook for telephony provider to verify login via Missed Call│
    └───────────────────────────────────────────────────────────────┘
    """
    # Providers usually send data in form-data or JSON.
    caller_id = request.POST.get('From') or request.GET.get('From') or parse_body(request).get('From')
    if not caller_id:
        return err('Caller ID missing')
    
    # Strip country code for matching if necessary, simplified for now
    caller_id = caller_id.replace('+', '').strip()
    if caller_id.startswith('91') and len(caller_id) == 12:
        caller_id = '+' + caller_id
    elif len(caller_id) == 10:
        caller_id = '+91' + caller_id
        
    try:
        profile = UserProfile.objects.get(mobile=caller_id)
        # Log them in via a session token or mark a flag in DB that polling client can read.
        # Since this is a webhook to the provider, we just return success.
        # In a real app, you would use channels/websockets or polling to tell the frontend.
        # Here we just mark a specific OTP record as verified to be polled.
        OTP.objects.create(identifier=caller_id, otp_code='MISSED', purpose='login', is_used=True)
        return ok(message='Missed call processed successfully')
    except UserProfile.DoesNotExist:
        return err('No account linked to this number')


@csrf_exempt
def api_verify_register(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/auth/verify-register/                              │
    │  Body: { identifier, otp, username, password, full_name,     │
    │          mobile }                                             │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    data       = parse_body(request)
    identifier = data.get('identifier', '').strip()
    otp_code   = data.get('otp', '').strip()
    username   = data.get('username', '').strip()
    password   = data.get('password', '').strip()
    full_name  = data.get('full_name', '').strip()
    mobile     = data.get('mobile', '').strip()

    if not all([identifier, otp_code, username, password]):
        return err('All fields are required')

    otp = OTP.objects.filter(identifier=identifier, otp_code=otp_code, is_used=False, purpose='register').first()
    if not otp or not otp.is_valid():
        if otp:
            otp.attempts += 1; otp.save()
        return err('Invalid or expired OTP')

    if User.objects.filter(username=username).exists():
        return err('Username already taken')

    names  = full_name.split(' ', 1)
    user   = User.objects.create_user(
        username=username, password=password,
        email=identifier if '@' in identifier else '',
        first_name=names[0],
        last_name=names[1] if len(names) > 1 else ''
    )
    UserProfile.objects.create(user=user, mobile=mobile, is_verified=True)
    otp.is_used = True; otp.save()
    login(request, user)
    return ok(redirect='/dashboard/')


@csrf_exempt
def api_verify_login(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/auth/verify-login/                                 │
    │  Body: { identifier, otp, password (optional) }              │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    data       = parse_body(request)
    identifier = data.get('identifier', '').strip()
    otp_code   = data.get('otp', '').strip()
    password   = data.get('password', '').strip()

    otp = OTP.objects.filter(identifier=identifier, otp_code=otp_code, is_used=False, purpose='login').first()
    if not otp or not otp.is_valid():
        if otp:
            otp.attempts += 1; otp.save()
        return err('Invalid or expired OTP')

    user = None
    if '@' in identifier:
        user = User.objects.filter(email=identifier).first()
    else:
        try:
            profile = UserProfile.objects.get(mobile=identifier)
            user    = profile.user
        except UserProfile.DoesNotExist:
            pass

    if not user:
        return err('No account found with this email/mobile')
    if password and not user.check_password(password):
        return err('Invalid password')

    otp.is_used = True; otp.save()
    login(request, user)
    return ok(redirect='/dashboard/')


# ═══════════════════════════════════════════════════════════
# ██  CROP PLANNER APIs
# ═══════════════════════════════════════════════════════════

@csrf_exempt
@login_required(login_url='/')
def api_crop_add(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/crop/add/                                          │
    │  Body: { crop_name, variety, season, field_area,             │
    │          sowing_date, expected_harvest, soil_type,           │
    │          irrigation_method, notes }                           │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d = parse_body(request)
    required = ['crop_name', 'season', 'field_area', 'sowing_date', 'expected_harvest']
    if not all(d.get(k) for k in required):
        return err('Missing required fields: ' + ', '.join(required))

    crop = CropPlan.objects.create(
        user=request.user,
        crop_name=d['crop_name'],
        variety=d.get('variety', ''),
        season=d['season'],
        field_area=float(d['field_area']),
        sowing_date=d['sowing_date'],
        expected_harvest=d['expected_harvest'],
        soil_type=d.get('soil_type', ''),
        irrigation_method=d.get('irrigation_method', ''),
        notes=d.get('notes', ''),
    )
    return ok(id=crop.id, crop=crop.crop_name, message='Crop plan saved successfully')


@csrf_exempt
@login_required(login_url='/')
def api_crop_delete(request, pk):
    """
    ┌────────────────────────────────────┐
    │  GET /api/crop/delete/<id>/        │
    └────────────────────────────────────┘
    """
    crop = get_object_or_404(CropPlan, pk=pk, user=request.user)
    crop.delete()
    return ok(message='Crop plan deleted')


@login_required(login_url='/')
def api_crop_list(request):
    """
    ┌────────────────────────────────────┐
    │  GET /api/crop/list/               │
    └────────────────────────────────────┘
    """
    crops = CropPlan.objects.filter(user=request.user).values(
        'id','crop_name','variety','season','field_area',
        'sowing_date','expected_harvest','status','created_at'
    )
    return ok(crops=list(crops))


# ═══════════════════════════════════════════════════════════
# ██  DISEASE RECOGNITION APIs
# ═══════════════════════════════════════════════════════════

@csrf_exempt
@login_required(login_url='/')
def api_disease_analyze(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/disease/analyze/                                   │
    │  Form-data: image (file), crop_name (text)                   │
    │  Uses trained ML model if available, else rule-based fallback │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    image_file = request.FILES.get('image')
    crop_name  = request.POST.get('crop_name', 'Unknown').strip()

    if not image_file:
        return err('No image file provided')

    # ── Validate image type ──────────────────────────────
    allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
    if image_file.content_type not in allowed:
        return err('Invalid file type. Please upload JPG, PNG, or WebP')

    # ── Save to DB first ──────────────────────────────────
    record = DiseaseRecord.objects.create(
        user=request.user,
        crop_name=crop_name,
        image=image_file,
    )

    # ── Run ML prediction ─────────────────────────────────
    try:
        from .ml.disease_engine import predict_disease
        record.image.open()
        result = predict_disease(record.image)
        record.image.close()
    except Exception as e:
        result = {
            'disease': 'Analysis Error', 'confidence': 0,
            'severity': 'Unknown', 'treatment': f'Error: {e}',
            'model_used': 'error', 'all_predictions': []
        }

    # ── Update record ──────────────────────────────────────
    record.detected_disease         = result['disease']
    record.confidence_score         = result['confidence']
    record.severity                 = result['severity']
    record.treatment_recommendation = result['treatment']
    record.all_predictions          = result.get('all_predictions', [])
    record.model_used               = result.get('model_used', 'rule_based')
    record.analyzed_at              = timezone.now()
    record.save()

    return ok(
        disease     = result['disease'],
        confidence  = result['confidence'],
        severity    = result['severity'],
        treatment   = result['treatment'],
        all_predictions = result.get('all_predictions', []),
        model_used  = result.get('model_used', 'rule_based'),
        record_id   = record.id,
        image_url   = record.image.url,
    )


@csrf_exempt
@login_required(login_url='/')
def api_disease_upload_dataset(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/disease/upload-dataset/                            │
    │  Form-data: csv_file (file), name (text), description (text) │
    │                                                               │
    │  CSV FORMAT:                                                  │
    │  Required column: label                                       │
    │  Optional feature cols: r_mean, g_mean, b_mean, r_std,       │
    │    g_std, b_std, hue_mean, sat_mean, val_mean, dx, dy,       │
    │    gray_mean, gray_std, r_ratio, g_ratio, b_ratio            │
    │  OR: image_path column (features auto-extracted)             │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    csv_file    = request.FILES.get('csv_file')
    name        = request.POST.get('name', 'My Dataset').strip()
    description = request.POST.get('description', '').strip()

    if not csv_file:
        return err('No CSV file provided')
    if not csv_file.name.endswith('.csv'):
        return err('File must be a .csv file')
    if csv_file.size > 50 * 1024 * 1024:
        return err('File too large. Max 50MB')

    # ── Quick validation: count rows and check label column ──
    try:
        import csv as csv_module
        content     = csv_file.read().decode('utf-8-sig', errors='replace')
        csv_file.seek(0)
        reader      = csv_module.DictReader(content.splitlines())
        rows        = list(reader)
        if not rows:
            return err('CSV file is empty')
        if 'label' not in rows[0]:
            return err('CSV must have a "label" column with disease names')
        total_rows   = len(rows)
        label_names  = list(set(r['label'].strip() for r in rows if r.get('label')))
        unique_count = len(label_names)
    except Exception as e:
        return err(f'Could not parse CSV: {e}')

    # ── Save dataset record ───────────────────────────────
    dataset = DiseaseDataset.objects.create(
        uploaded_by  = request.user,
        name         = name,
        description  = description,
        csv_file     = csv_file,
        total_rows   = total_rows,
        unique_labels= unique_count,
        label_names  = label_names,
        status       = 'uploaded',
    )

    return ok(
        dataset_id   = dataset.id,
        name         = dataset.name,
        total_rows   = total_rows,
        unique_labels= unique_count,
        label_names  = label_names,
        message      = f'Dataset uploaded! {total_rows} rows, {unique_count} disease classes. Ready to train.',
    )


@csrf_exempt
@login_required(login_url='/')
def api_disease_train(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/disease/train/                                     │
    │  Body: { dataset_id: <int> }                                 │
    │  Trains ML model in background thread.                        │
    │  Returns immediately; poll /api/disease/model-status/        │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d          = parse_body(request)
    dataset_id = d.get('dataset_id')

    if not dataset_id:
        return err('dataset_id is required')

    dataset = get_object_or_404(DiseaseDataset, id=dataset_id, uploaded_by=request.user)

    if dataset.status == 'training':
        return err('Training already in progress for this dataset')

    dataset.status = 'training'
    dataset.training_log = 'Training started...'
    dataset.save()

    return ok(
        dataset_id = dataset.id,
        message    = '🚀 CNN training is now handled via the command line script: python train_cnn.py',
    )


@login_required(login_url='/')
def api_model_status(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  GET /api/disease/model-status/                               │
    │  Returns current model status and accuracy                    │
    └───────────────────────────────────────────────────────────────┘
    """
    trained = os.path.exists(str(settings.DISEASE_MODEL_PATH))

    latest_dataset = DiseaseDataset.objects.filter(
        uploaded_by=request.user
    ).order_by('-uploaded_at').first()

    status_info = {
        'model_exists': trained,
        'model_path':   str(settings.DISEASE_MODEL_PATH),
    }

    if latest_dataset:
        status_info.update({
            'dataset_id':    latest_dataset.id,
            'dataset_name':  latest_dataset.name,
            'status':        latest_dataset.status,
            'accuracy':      latest_dataset.accuracy,
            'label_names':   latest_dataset.label_names,
            'total_rows':    latest_dataset.total_rows,
            'unique_labels': latest_dataset.unique_labels,
            'training_log':  latest_dataset.training_log[-2000:] if latest_dataset.training_log else '',
            'trained_at':    str(latest_dataset.trained_at) if latest_dataset.trained_at else None,
        })

    return ok(**status_info)


@login_required(login_url='/')
def api_dataset_list(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  GET /api/disease/dataset-list/                               │
    └───────────────────────────────────────────────────────────────┘
    """
    datasets = DiseaseDataset.objects.filter(uploaded_by=request.user).values(
        'id','name','status','total_rows','unique_labels',
        'label_names','accuracy','uploaded_at','trained_at'
    )
    return ok(datasets=list(datasets))

@csrf_exempt
@login_required(login_url='/')
def api_disease_auto_setup(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/disease/auto-setup/                                │
    │  Automatically generate a robust sample dataset and trigger  │
    │  training, avoiding manual upload.                            │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)
    
    import random
    from django.core.files.base import ContentFile
    
    # Generate CSV content for 4 diseases with somewhat separated synthetic features
    diseases = ['Healthy', 'Early Blight', 'Yellow Rust', 'Leaf Spot']
    csv_lines = ['label,r_mean,g_mean,b_mean,r_std,g_std,b_std,h_mean,s_mean,v_mean,dx,dy,gray_mean,gray_std,r_ratio,g_ratio,b_ratio']
    
    total_rows = 150
    for _ in range(total_rows):
        disease = random.choice(diseases)
        if disease == 'Healthy':
            # High Green
            r, g, b = random.randint(50, 100), random.randint(150, 220), random.randint(50, 100)
        elif disease == 'Yellow Rust':
            # High Red and Green (Yellow)
            r, g, b = random.randint(180, 240), random.randint(180, 240), random.randint(30, 80)
        elif disease == 'Early Blight':
            # Brownish/Dark
            r, g, b = random.randint(100, 150), random.randint(80, 120), random.randint(50, 80)
        else: # Leaf Spot
            # Mixed
            r, g, b = random.randint(120, 180), random.randint(120, 180), random.randint(100, 150)
            
        r_std, g_std, b_std = random.uniform(5, 20), random.uniform(5, 20), random.uniform(5, 20)
        h, s, v = random.uniform(20, 80), random.uniform(100, 200), random.uniform(100, 200)
        dx, dy = random.uniform(10, 40), random.uniform(10, 40)
        gray_m, gray_s = (r*0.299 + g*0.587 + b*0.114), random.uniform(10, 30)
        tot = r + g + b + 0.001
        rr, gr, br = r/tot, g/tot, b/tot
        
        csv_lines.append(f"{disease},{r},{g},{b},{r_std:.1f},{g_std:.1f},{b_std:.1f},{h:.1f},{s:.1f},{v:.1f},{dx:.1f},{dy:.1f},{gray_m:.1f},{gray_s:.1f},{rr:.3f},{gr:.3f},{br:.3f}")
        
    csv_content = "\\n".join(csv_lines)
    
    dataset = DiseaseDataset.objects.create(
        uploaded_by=request.user,
        name='Auto-Generated Standard Dataset',
        description='A synthetic robust dataset with 4 categories automatically generated.',
        total_rows=total_rows,
        unique_labels=4,
        label_names=diseases,
        status='training',
    )
    dataset.csv_file.save('auto_dataset.csv', ContentFile(csv_content))
    dataset.training_log = 'Training started automatically...'
    dataset.save()
    
    return ok(message='Dataset generated! Please run train_cnn.py to train the model.')


# ═══════════════════════════════════════════════════════════
# ██  PEST CONTROL APIs
# ═══════════════════════════════════════════════════════════

# Pest treatment database
PEST_DB = {
    'aphids':     {'pesticide':'Imidacloprid 17.8 SL',    'dosage':'0.5ml/L','organic':'Neem oil 5ml/L, Ladybird beetle release',     'method':'Foliar spray early morning'},
    'whitefly':   {'pesticide':'Thiamethoxam 25 WG',      'dosage':'0.3g/L', 'organic':'Yellow sticky traps, Reflective mulch',        'method':'Spray leaf undersides'},
    'bollworm':   {'pesticide':'Chlorpyrifos 20 EC',      'dosage':'2ml/L',  'organic':'Bt spray, Pheromone traps at 5/acre',          'method':'Spray at egg hatching stage'},
    'armyworm':   {'pesticide':'Spinosad 45 SC',          'dosage':'0.5ml/L','organic':'Metarhizium anisopliae bio-pesticide',          'method':'Evening spray'},
    'thrips':     {'pesticide':'Fipronil 5 SC',           'dosage':'1.5ml/L','organic':'Blue sticky traps, Spinosad 0.5ml/L',           'method':'Spray on new growth'},
    'mites':      {'pesticide':'Abamectin 1.8 EC',        'dosage':'0.5ml/L','organic':'Neem oil + soap solution, Predatory mites',     'method':'Spray leaf undersides, repeat after 7 days'},
    'jassid':     {'pesticide':'Dimethoate 30 EC',        'dosage':'1ml/L',  'organic':'Tobacco decoction spray',                       'method':'Foliar spray'},
    'mealybug':   {'pesticide':'Buprofezin 25 SC',        'dosage':'1.5ml/L','organic':'Alcohol + soap spray, Cryptolaemus release',    'method':'Spray on colonies'},
    'cutworm':    {'pesticide':'Chlorpyrifos 20 EC',      'dosage':'3ml/L soil drench','organic':'Entomopathogenic nematodes',           'method':'Soil application near stem'},
    'leafminer':  {'pesticide':'Abamectin 1.8 EC',        'dosage':'0.5ml/L','organic':'Pheromone traps, Neem oil 3ml/L',              'method':'Spray at first sign of mines'},
}

@csrf_exempt
@login_required(login_url='/')
def api_pest_add(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/pest/add/                                          │
    │  Body: { crop_name, pest_name, severity,                     │
    │          affected_area, symptoms }                            │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d       = parse_body(request)
    pest_key= d.get('pest_name', '').lower().strip()
    rec     = PEST_DB.get(pest_key, {
        'pesticide': 'Consult local agronomist',
        'dosage': 'As per label',
        'organic': 'Neem oil 5ml/L spray',
        'method': 'Foliar application'
    })

    record = PestControlRecord.objects.create(
        user=request.user,
        crop_name=d.get('crop_name', ''),
        pest_name=d.get('pest_name', ''),
        severity=d.get('severity', 'medium'),
        affected_area=float(d.get('affected_area', 1)),
        symptoms=d.get('symptoms', ''),
        recommended_pesticide=rec['pesticide'],
        dosage=rec['dosage'],
        application_method=rec['method'],
        organic_alternative=rec['organic'],
        ai_recommendation=(
            f"Treat {d.get('pest_name','')} immediately. "
            f"Use {rec['pesticide']} at {rec['dosage']}. {rec['method']}."
        )
    )
    return ok(
        record_id      = record.id,
        pesticide      = rec['pesticide'],
        dosage         = rec['dosage'],
        organic        = rec['organic'],
        method         = rec['method'],
        recommendation = record.ai_recommendation,
    )


@csrf_exempt
@login_required(login_url='/')
def api_pest_resolve(request, pk):
    """
    ┌────────────────────────────────────┐
    │  POST /api/pest/resolve/<id>/      │
    └────────────────────────────────────┘
    """
    record = get_object_or_404(PestControlRecord, pk=pk, user=request.user)
    record.resolved = True
    record.save()
    return ok(message='Pest record marked as resolved')


# ═══════════════════════════════════════════════════════════
# ██  FERTILIZER APIs
# ═══════════════════════════════════════════════════════════

# NPK requirements per acre (kg)
NPK_DB = {
    'wheat':     {'N':60, 'P':30, 'K':30},
    'rice':      {'N':80, 'P':40, 'K':40},
    'maize':     {'N':100,'P':50, 'K':50},
    'tomato':    {'N':75, 'P':60, 'K':80},
    'potato':    {'N':90, 'P':60, 'K':90},
    'cotton':    {'N':80, 'P':40, 'K':40},
    'sugarcane': {'N':150,'P':60, 'K':60},
    'soybean':   {'N':20, 'P':60, 'K':40},
    'groundnut': {'N':25, 'P':50, 'K':50},
    'mustard':   {'N':60, 'P':30, 'K':30},
    'onion':     {'N':75, 'P':50, 'K':60},
    'sunflower': {'N':60, 'P':60, 'K':30},
}

STAGE_FACTORS  = {'seedling':0.2, 'vegetative':0.4, 'flowering':0.25, 'fruiting':0.15}
FERTILIZER_COST= {'urea':6.5, 'dap':27.0, 'mop':17.5}   # ₹ per kg

@csrf_exempt
@login_required(login_url='/')
def api_fertilizer_calc(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/fertilizer/calculate/                              │
    │  Body: { crop_name, field_area, soil_type, crop_stage }      │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d     = parse_body(request)
    crop  = d.get('crop_name', '').lower().strip()
    area  = float(d.get('field_area', 1))
    soil  = d.get('soil_type', 'loamy')
    stage = d.get('crop_stage', 'vegetative')

    if area <= 0:
        return err('Field area must be greater than 0')

    npk    = NPK_DB.get(crop, {'N':60,'P':30,'K':30})
    factor = STAGE_FACTORS.get(stage, 0.4)

    # Soil adjustment factors
    soil_adj = {'sandy':1.2, 'clay':0.9, 'loamy':1.0, 'black':0.85, 'red':1.1, 'silty':0.95}
    adj      = soil_adj.get(soil, 1.0)
    
    # Advanced: Existing Soil Test NPK (kg/acre)
    soil_n = float(d.get('soil_n', 0))
    soil_p = float(d.get('soil_p', 0))
    soil_k = float(d.get('soil_k', 0))

    # Calculate required, subtracting existing soil nutrients
    n = max(0, round(npk['N'] * area * factor * adj - soil_n, 1))
    p = max(0, round(npk['P'] * area * factor * adj - soil_p, 1))
    k = max(0, round(npk['K'] * area * factor * adj - soil_k, 1))

    urea = round(n / 0.46, 1)
    dap  = round(p / 0.18, 1)
    mop  = round(k / 0.60, 1)

    cost = round(
        urea * FERTILIZER_COST['urea'] +
        dap  * FERTILIZER_COST['dap']  +
        mop  * FERTILIZER_COST['mop'], 2
    )

    schedule = (
        f"Week 1: Apply {round(n*0.5,1)}kg N (Urea: {round(urea*0.5,1)}kg) + full DAP ({dap}kg) + full MOP ({mop}kg) as basal dose. "
        f"Week 4: Top dress {round(n*0.3,1)}kg N (Urea: {round(urea*0.3,1)}kg). "
        f"Week 7: Final top dress {round(n*0.2,1)}kg N (Urea: {round(urea*0.2,1)}kg). "
        f"Apply in moist soil for best results."
    )
    
    # Organic alternative calculation (Vermicompost has approx 1.5% N, 1% P, 1% K)
    # We estimate based on Nitrogen requirement primarily
    vermi_req = round(n / 0.015, 0)
    organic_alt = (
        f"To substitute chemical fertilizers, you can apply approx {vermi_req} kg of Vermicompost or FYM (Farm Yard Manure). "
        f"Additionally, applying 5-10 kg of Neem Cake per acre helps control soil-borne pests and improves N-use efficiency."
    )

    log = FertilizerLog.objects.create(
        user=request.user,
        crop_name=d.get('crop_name',''),
        field_area=area,
        soil_type=soil,
        crop_stage=stage,
        nitrogen_kg=n,
        phosphorus_kg=p,
        potassium_kg=k,
        recommended_fertilizer=f'Urea:{urea}kg, DAP:{dap}kg, MOP:{mop}kg',
        application_schedule=schedule,
        estimated_cost=cost,
    )

    return ok(
        nitrogen=n, phosphorus=p, potassium=k,
        urea=urea, dap=dap, mop=mop,
        schedule=schedule, estimated_cost=cost,
        organic=organic_alt,
        log_id=log.id
    )


# ═══════════════════════════════════════════════════════════
# ██  WEATHER API
# ═══════════════════════════════════════════════════════════

@csrf_exempt
@login_required(login_url='/')
def api_weather(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/weather/                                           │
    │  Body: { lat, lon, location }                                │
    │  🔑 Requires: OPENWEATHER_API_KEY in settings.py             │
    │     Get free key: https://openweathermap.org/api             │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d    = parse_body(request)
    lat  = d.get('lat')
    lon  = d.get('lon')
    loc  = d.get('location', 'Unknown Location').strip()
    key  = settings.OPENWEATHER_API_KEY

    # ── Check if API key is configured ────────────────────
    if 'your_openweathermap' in key.lower():
        # Return demo data
        demo = {
            'temperature':28, 'feels_like':31, 'humidity':65,
            'wind_speed':12.5, 'condition':'Partly Cloudy',
            'icon':'02d', 'location':loc, 'country':'IN',
            'pressure':1012, 'visibility':10,
        }
        return ok(
            current  = demo,
            forecast = _demo_forecast(),
            advisory = farming_advisory(28, 65, 'partly cloudy'),
            demo     = True,
            message  = '⚠️ Demo data. Set OPENWEATHER_API_KEY in settings.py for live weather.',
        )

    try:
        base = settings.OPENWEATHER_BASE_URL
        if lat and lon:
            params = f'lat={lat}&lon={lon}'
        else:
            params = f'q={loc}'

        # Current weather
        resp = requests.get(f'{base}/weather?{params}&appid={key}&units=metric', timeout=8)
        wd   = resp.json()
        if wd.get('cod') != 200:
            raise Exception(wd.get('message', 'Location not found'))

        current = {
            'temperature':  round(wd['main']['temp']),
            'feels_like':   round(wd['main']['feels_like']),
            'humidity':     wd['main']['humidity'],
            'wind_speed':   round(wd['wind']['speed'] * 3.6, 1),
            'condition':    wd['weather'][0]['description'].title(),
            'icon':         wd['weather'][0]['icon'],
            'location':     wd.get('name', loc),
            'country':      wd.get('sys', {}).get('country', ''),
            'pressure':     wd['main']['pressure'],
            'visibility':   wd.get('visibility', 0) // 1000,
        }

        # 5-day forecast
        fr   = requests.get(f'{base}/forecast?{params}&appid={key}&units=metric', timeout=8).json()
        forecast = []
        seen = set()
        for item in fr.get('list', []):
            date = item['dt_txt'].split(' ')[0]
            if date not in seen and len(forecast) < 5:
                seen.add(date)
                forecast.append({
                    'date':      date,
                    'temp_max':  round(item['main']['temp_max']),
                    'temp_min':  round(item['main']['temp_min']),
                    'condition': item['weather'][0]['description'].title(),
                    'icon':      item['weather'][0]['icon'],
                    'humidity':  item['main']['humidity'],
                })

        WeatherLog.objects.create(
            user=request.user, location=current['location'],
            latitude=lat, longitude=lon,
            temperature=current['temperature'],
            humidity=current['humidity'],
            wind_speed=current['wind_speed'],
            weather_condition=current['condition'],
            forecast_data={'forecast': forecast},
            farming_advisory=farming_advisory(current['temperature'], current['humidity'], current['condition']),
        )

        return ok(
            current  = current,
            forecast = forecast,
            advisory = farming_advisory(current['temperature'], current['humidity'], current['condition']),
        )

    except Exception as e:
        demo = {
            'temperature':28,'feels_like':31,'humidity':65,
            'wind_speed':12.5,'condition':'Partly Cloudy',
            'icon':'02d','location':loc,'country':'IN','pressure':1012,'visibility':10,
        }
        return ok(
            current  = demo,
            forecast = _demo_forecast(),
            advisory = farming_advisory(28, 65, 'partly cloudy'),
            demo     = True,
            message  = f'Live weather unavailable: {e}. Showing demo data.',
        )


def _demo_forecast():
    import datetime
    conditions = ['Sunny','Partly Cloudy','Cloudy','Light Rain','Sunny']
    icons      = ['01d','02d','03d','10d','01d']
    today      = datetime.date.today()
    forecast   = []
    for i in range(5):
        d = today + datetime.timedelta(days=i+1)
        forecast.append({
            'date': str(d), 'temp_max': 30-i, 'temp_min': 20+i,
            'condition': conditions[i], 'icon': icons[i], 'humidity': 60+i*3,
        })
    return forecast


# ═══════════════════════════════════════════════════════════
# ██  CHATBOT API
# ═══════════════════════════════════════════════════════════

@csrf_exempt
@login_required(login_url='/')
def api_chatbot(request):
    """
    ┌───────────────────────────────────────────────────────────────┐
    │  POST /api/chatbot/                                           │
    │  JSON: { message, context }                                   │
    │  OR multipart: message + image file                           │
    └───────────────────────────────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    if request.content_type and 'multipart' in request.content_type:
        message    = request.POST.get('message', '')
        context    = request.POST.get('context', 'general')
        image_file = request.FILES.get('image')
    else:
        d       = parse_body(request)
        message = d.get('message', '')
        context = d.get('context', 'general')
        image_file = None

    session_id = request.session.setdefault('chat_session', str(uuid.uuid4()))
    ChatHistory.objects.create(user=request.user, session_id=session_id, role='user', message=message, feature_context=context)

    response = _generate_chat_response(message, context, image_file, request.user)

    ChatHistory.objects.create(user=request.user, session_id=session_id, role='assistant', message=response, feature_context=context)
    return ok(response=response)


def _generate_chat_response(message, context, image_file, user):
    msg = message.lower()

    if context == 'disease' or any(w in msg for w in ['disease','blight','rust','yellow','brown','spot','sick','infected','leaf']):
        if image_file:
            from .ml.disease_engine import predict_disease
            try:
                # Read the file content for the engine
                image_bytes = image_file.read()
                result = predict_disease(image_bytes)
                
                disease = result['disease']
                confidence = result['confidence']
                treatment = result['treatment']
                
                return (f'🔬 I analyzed your image using our AI model! Here is what I found:\n\n'
                        f'**Disease Detected:** {disease} ({confidence}% confidence)\n\n'
                        f'**Recommended Treatment:**\n{treatment}\n\n'
                        f'For more details, please visit the **Disease AI** section. 🌿')
            except Exception as e:
                return f'⚠️ I encountered an error while analyzing the image: {str(e)}. Please try again or use the main Disease AI page.'
        return ('🌿 To diagnose crop diseases:\n\n'
                '1. Go to **Disease AI** section\n'
                '2. Upload a clear photo of the affected plant\n'
                '3. Select your crop type\n'
                '4. Click **Analyze Disease**\n\n'
                'I can identify 18+ diseases including Rust, Blight, Mosaic Virus, Blast, and more! 📸')

    import re
    import requests
    from django.conf import settings
    
    city_match = re.search(r'weather\s+(?:in|of|for|at)\s+([a-zA-Z\s]+)', msg)
    if city_match:
        city = city_match.group(1).strip()
        key = getattr(settings, 'OPENWEATHER_API_KEY', '')
        base = getattr(settings, 'OPENWEATHER_BASE_URL', 'https://api.openweathermap.org/data/2.5')
        
        if 'your_openweathermap' in key.lower() or not key:
            return f'🌤️ I see you want the weather in **{city.title()}**, but my live weather API key is not configured. Please set up the OPENWEATHER_API_KEY in settings.py!'
            
        try:
            resp = requests.get(f'{base}/weather?q={city}&appid={key}&units=metric', timeout=5)
            wd = resp.json()
            if wd.get('cod') == 200:
                temp = round(wd['main']['temp'])
                desc = wd['weather'][0]['description'].title()
                humidity = wd['main']['humidity']
                return (f'🌤️ **Live Weather for {wd["name"]}**:\n\n'
                        f'• **Temperature**: {temp}°C\n'
                        f'• **Condition**: {desc}\n'
                        f'• **Humidity**: {humidity}%\n\n'
                        f'For a full 5-day forecast and farming advisories, please visit the **Weather Forecast** section! 🚿')
            else:
                return f'⚠️ I could not find the weather for "{city.title()}". Please check the spelling or try another city.'
        except Exception as e:
            return f'⚠️ Sorry, I could not fetch the weather right now: {str(e)}'

    if context == 'weather' or any(w in msg for w in ['weather','rain','temperature','forecast','humidity','wind']):
        return ('🌤️ For weather forecasts:\n\n'
                '• Go to **Weather Forecast** section\n'
                '• Enable GPS location or search your city\n'
                '• Get 5-day forecast + farming advisories\n\n'
                'I recommend irrigating before 8 AM during hot weather! 🚿')

    if 'rice' in msg or 'paddy' in msg:
        return '🌾 **Rice (Paddy)** is a Kharif crop. It is typically sown in June-July (onset of monsoon) and harvested in October-November. It requires high temperature and heavy rainfall.'
    
    if 'wheat' in msg:
        return '🌾 **Wheat** is a Rabi crop. It is typically sown in October-December and harvested in February-April. It requires cool weather and moderate irrigation.'

    if 'maize' in msg or 'corn' in msg:
        return '🌽 **Maize (Corn)** is primarily a Kharif crop, sown in June-July and harvested in September-October, though it can also be grown in Rabi in some regions.'

    if 'mustard' in msg:
        return '🌼 **Mustard** is a Rabi crop. It is sown in October-November and harvested in February-March.'

    if 'cotton' in msg:
        return '🪴 **Cotton** is a Kharif crop. Sown in May-July and harvested in October-January. It requires clear sunshine during its growing period.'

    if context == 'crop' or any(w in msg for w in ['crop','sow','plant','harvest','kharif','rabi','zaid','season']):
        return ('🌾 Crop Planning Guide:\n\n'
                '• **Kharif** (Jun–Oct): Rice, Maize, Cotton, Soybean, Bajra\n'
                '• **Rabi** (Oct–Mar): Wheat, Mustard, Peas, Chickpea\n'
                '• **Zaid** (Mar–Jun): Watermelon, Cucumber, Bitter Gourd\n\n'
                'Use the **Crop Planner** to schedule with sowing/harvest dates! 📅')

    if any(w in msg for w in ['fertilizer','npk','urea','nutrient','nitrogen','phosphorus','potassium']):
        return ('💊 Fertilizer Tips:\n\n'
                '• **N (Urea)** → Leafy growth\n'
                '• **P (DAP)** → Root development & flowering\n'
                '• **K (MOP)** → Fruit quality & disease resistance\n\n'
                'Use our **Fertilizer Calculator** for precise kg/acre recommendations with cost estimate! 🧮')

    if any(w in msg for w in ['pest','insect','aphid','whitefly','worm','bug','mite']):
        return ('🐛 Pest Management:\n\n'
                '• Inspect crops early morning\n'
                '• Prefer organic: Neem oil 5ml/L water\n'
                '• Install sticky traps for flying pests\n'
                '• Use chemical pesticides only when >10% plants affected\n\n'
                'Log pests in **Pest Control** section for AI treatment plans! 🛡️')

    if any(w in msg for w in ['hello','hi','hey','namaste','namaskar','good']):
        return (f'🌿 Namaste {user.first_name}! Welcome to **AgriBot**!\n\n'
                'I can help you with:\n'
                '🌤️ Weather forecasts\n'
                '🔬 Disease diagnosis\n'
                '🌾 Crop planning\n'
                '💊 Fertilizer calc\n'
                '🐛 Pest control\n\n'
                'How can I help you today? 🚜')

    return ('🌱 I\'m AgriBot, your AI farming assistant!\n\n'
            'Ask me about: crop planning, disease diagnosis, weather, fertilizer, or pest control.\n'
            'You can also switch context tabs above for specialized help! 🌿')


# ═══════════════════════════════════════════════════════════
# ██  CONTACT API
# ═══════════════════════════════════════════════════════════

@csrf_exempt
def api_contact(request):
    """
    ┌────────────────────────────────────┐
    │  POST /api/contact/                │
    │  Body: { name, email, subject,    │
    │          message }                 │
    └────────────────────────────────────┘
    """
    if request.method != 'POST':
        return err('Method not allowed', 405)

    d = parse_body(request)
    if not all(d.get(k) for k in ('name','email','subject','message')):
        return err('All fields are required')

    from django.core.mail import send_mail
    from django.conf import settings

    ContactInquiry.objects.create(**{k: d[k] for k in ('name','email','subject','message')})
    
    # Try sending email notification to support email
    try:
        support_email = 'shivamshah3111@gmail.com'
        full_message = f"Name: {d['name']}\nEmail: {d['email']}\n\nMessage:\n{d['message']}"
        send_mail(
            subject=f"[AgriAI Contact] {d['subject']}",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[support_email],
            fail_silently=True,
        )
    except Exception:
        pass
        
    return ok(message='Message received! We\'ll respond within 24 hours. 🌿')
