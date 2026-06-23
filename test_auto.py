import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agriai.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from agriai_app.views import api_disease_auto_setup
import json

factory = RequestFactory()
request = factory.post('/api/disease/auto-setup/')
request.user, _ = User.objects.get_or_create(username='test_user')

response = api_disease_auto_setup(request)
print("Response status:", response.status_code)

import time
print("Waiting for training to complete...")
time.sleep(10)

dataset = DiseaseDataset.objects.get(name='Auto-Generated Standard Dataset')
print("Status:", dataset.status)
print("Accuracy:", dataset.accuracy)
print("Model Path exists:", os.path.exists(dataset.model_path) if dataset.model_path else False)
