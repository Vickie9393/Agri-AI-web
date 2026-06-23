# 🌿 AgriAI v2 — Complete Setup & API Reference

## ⚡ Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py makemigrations agriai_app
python manage.py migrate

# 4. Create admin user
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
# → Open: http://127.0.0.1:8000/
```

---

## 🔑 API Keys to Configure (in `agriai/settings.py`)

| Key | Where to Get | Used For |
|-----|-------------|----------|
| `EMAIL_HOST_USER` | Your Gmail address | OTP emails |
| `EMAIL_HOST_PASSWORD` | Gmail → Settings → Security → App Passwords | OTP emails |
| `TWILIO_ACCOUNT_SID` | twilio.com → Console | SMS OTP (optional) |
| `TWILIO_AUTH_TOKEN` | twilio.com → Console | SMS OTP (optional) |
| `TWILIO_PHONE_NUMBER` | twilio.com → Buy a number | SMS OTP (optional) |
| `OPENWEATHER_API_KEY` | openweathermap.org/api (free tier) | Weather forecast |

---

## 🌐 All API Endpoints

### AUTH
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/auth/send-otp/` | `{identifier, type, purpose}` | Send OTP via email/SMS |
| POST | `/api/auth/verify-login/` | `{identifier, otp, password}` | Login with OTP |
| POST | `/api/auth/verify-register/` | `{identifier, otp, username, password, full_name, mobile}` | Register with OTP |

### CROP PLANNER
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/crop/add/` | `{crop_name, season, field_area, sowing_date, expected_harvest}` | Add crop plan |
| GET | `/api/crop/list/` | — | List all crop plans |
| GET | `/api/crop/delete/<id>/` | — | Delete a crop plan |

### DISEASE RECOGNITION
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/disease/analyze/` | `form-data: image, crop_name` | Analyze disease from image |
| POST | `/api/disease/upload-dataset/` | `form-data: csv_file, name, description` | Upload CSV training dataset |
| POST | `/api/disease/train/` | `{dataset_id}` | Train ML model from dataset |
| GET | `/api/disease/model-status/` | — | Check training status + accuracy |
| GET | `/api/disease/dataset-list/` | — | List all uploaded datasets |

### PEST CONTROL
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/pest/add/` | `{crop_name, pest_name, severity, affected_area, symptoms}` | Log pest + get recommendation |
| POST | `/api/pest/resolve/<id>/` | — | Mark pest as resolved |

### FERTILIZER
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/fertilizer/calculate/` | `{crop_name, field_area, soil_type, crop_stage}` | Calculate NPK + cost |

### WEATHER
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/weather/` | `{lat, lon, location}` | Get weather + forecast + advisory |

### CHATBOT
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/chatbot/` | `{message, context}` or `form-data: message, image` | Chat with AgriBot |

### CONTACT
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/contact/` | `{name, email, subject, message}` | Submit contact inquiry |

---

## 🧠 Disease ML Model — CSV Format

Upload a CSV file with the following columns:

**Required:** `label` (disease name)

**Option A — Pre-computed Features (recommended):**
```
label, r_mean, g_mean, b_mean, r_std, g_std, b_std,
hue_mean, sat_mean, val_mean, dx, dy,
gray_mean, gray_std, r_ratio, g_ratio, b_ratio
```

**Option B — Image Paths:**
```
label, image_path
```
Features will be auto-extracted from each image.

**Example:**
```csv
label,r_mean,g_mean,b_mean,...
Healthy,78,155,68,...
Yellow Rust,182,158,62,...
Blast Disease,42,48,52,...
```

A **sample dataset** with 70 rows across 10 disease classes is included at:
`media/datasets/sample_disease_dataset.csv`

---

## 📁 Project Structure

```
agriai_v2/
├── agriai/
│   ├── settings.py          ← 🔑 All API keys here
│   ├── urls.py
│   └── wsgi.py
├── agriai_app/
│   ├── models.py            ← All 10 database models
│   ├── views.py             ← All APIs with full documentation
│   ├── urls.py              ← All 18 URL routes
│   ├── admin.py
│   └── ml/
│       └── disease_engine.py ← CSV trainer + image predictor
├── templates/agriai/
│   ├── auth.html
│   ├── base.html            ← Nav + Chatbot + Contact
│   ├── dashboard.html
│   ├── crop_planner.html
│   ├── disease_recognition.html ← Image upload + CSV train + history tabs
│   ├── pest_control.html
│   ├── fertilizer.html
│   └── weather.html
├── static/
│   ├── css/ (auth, base, dashboard, features, disease_ml)
│   └── js/  (auth, base, crop_planner, disease, pest_control, fertilizer, weather)
├── media/
│   └── datasets/
│       └── sample_disease_dataset.csv  ← 70 rows, 10 disease classes
├── requirements.txt
└── manage.py
```

---

## 🌿 Diseases Supported (18 classes)

Healthy, Yellow Rust, Brown Rust, Early Blight, Late Blight,
Powdery Mildew, Blast Disease, Leaf Spot, Bacterial Blight,
Mosaic Virus, Fusarium Wilt, Root Rot, Cercospora Leaf Spot,
Crown Rot, Smut, Sheath Blight, Anthracnose, Downy Mildew
