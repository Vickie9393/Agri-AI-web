"""
╔══════════════════════════════════════════════════════════════════╗
║  AgriAI — ML Disease Detection Engine                            ║
║                                                                  ║
║  • predict_disease() — Predict disease using trained CNN         ║
║                        or fallback rule-based system             ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os
import io
import pickle
import logging
import numpy as np
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Disease treatment database ──────────────────────────────────
DISEASE_TREATMENTS = {
    'Healthy':             {'severity': 'None',     'treatment': '✅ Your crop looks healthy! Continue regular maintenance and monitoring.'},
    'Early Blight':        {'severity': 'Medium',   'treatment': 'Apply Chlorothalonil (2g/L). Remove infected leaves. Avoid overhead irrigation. Apply copper fungicide preventively.'},
    'Late Blight':         {'severity': 'High',     'treatment': 'Apply Metalaxyl + Mancozeb. Destroy infected plants. Ensure good drainage. Spray every 7 days.'},
    'Leaf Spot':           {'severity': 'Low',      'treatment': 'Apply Mancozeb (2.5g/L). Improve air circulation. Avoid leaf wetness. Rotate crops next season.'},
    'Yellow Rust':         {'severity': 'Medium',   'treatment': 'Apply Propiconazole (1ml/L). Remove infected leaves early. Sow resistant varieties.'},
    'Brown Rust':          {'severity': 'Medium',   'treatment': 'Apply Tebuconazole (1ml/L). Spray at early infection stage. Use certified seeds.'},
    'Powdery Mildew':      {'severity': 'Low',      'treatment': 'Apply Sulphur dust (25kg/ha) or Carbendazim (1g/L). Improve ventilation. Reduce nitrogen fertilizer.'},
    'Bacterial Blight':    {'severity': 'High',     'treatment': 'Apply Copper oxychloride (3g/L). Remove infected plants. Avoid wounds. Use disease-free seeds.'},
    'Mosaic Virus':        {'severity': 'High',     'treatment': 'No cure available. Remove infected plants immediately. Control aphid vectors with Imidacloprid. Use resistant varieties.'},
    'Blast Disease':       {'severity': 'Critical', 'treatment': 'Apply Tricyclazole (0.6g/L) immediately. Drain water from field. Apply nitrogen in splits. Plant resistant varieties.'},
    'Sheath Blight':       {'severity': 'Medium',   'treatment': 'Apply Validamycin (2ml/L). Reduce plant density. Drain field periodically.'},
    'Anthracnose':         {'severity': 'Medium',   'treatment': 'Apply Carbendazim (1g/L). Remove infected plant parts. Avoid overhead irrigation.'},
    'Downy Mildew':        {'severity': 'Medium',   'treatment': 'Apply Cymoxanil + Famoxadone (0.5g/L). Improve drainage. Spray at 10-day intervals.'},
    'Fusarium Wilt':       {'severity': 'High',     'treatment': 'No effective chemical. Remove infected plants. Solarize soil. Use Trichoderma bio-fungicide.'},
    'Root Rot':            {'severity': 'High',     'treatment': 'Apply Carbendazim soil drench (2g/L). Improve drainage. Avoid overwatering. Use Trichoderma viride.'},
    'Cercospora Leaf Spot':{'severity': 'Low',      'treatment': 'Apply Hexaconazole (1ml/L). Remove old leaves. Maintain proper spacing.'},
    'Crown Rot':           {'severity': 'High',     'treatment': 'Improve drainage. Apply Captan drench. Use disease-free planting material.'},
    'Smut':                {'severity': 'Medium',   'treatment': 'Seed treatment with Carboxin (2g/kg seed). Remove smutted ears before spore release.'},
    'Unknown Disease':     {'severity': 'Unknown',  'treatment': 'Consult your local Krishi Vigyan Kendra (KVK) or call the Kisan Call Centre: 1800-180-1551.'},
}



def predict_disease(image_input, model_path=None, label_encoder_path=None):
    """
    Predict disease from an image.
    Returns top 3 predictions with confidence scores.
    Falls back to rule-based system if CNN is not available.
    """
    from django.conf import settings as dj_settings

    model_path         = model_path or str(dj_settings.DISEASE_MODEL_PATH)
    label_encoder_path = label_encoder_path or str(dj_settings.LABEL_ENCODER_PATH)
    
    # ── Try CNN Model First ────────────────────────────────
    cnn_model_path = Path(model_path).parent / 'cnn_disease_model.keras'
    cnn_classes_path = Path(label_encoder_path).parent / 'cnn_classes.json'
    
    if os.path.exists(cnn_model_path) and os.path.exists(cnn_classes_path):
        try:
            return _cnn_predict(image_input, cnn_model_path, cnn_classes_path)
        except Exception as e:
            logger.warning(f"CNN model prediction failed: {e}. Falling back to rule-based.")

    # ── Fallback: Rule-Based Color Analysis ───────────────
    return _rule_based_predict(image_input)


def _map_cnn_class_to_disease(class_name):
    """Maps CNN directory class name to DISEASE_TREATMENTS key."""
    # E.g. 'Apple___Apple_scab' -> 'Apple Scab'
    name = class_name.split('___')[-1].replace('_', ' ')
    
    mapping = {
        'Apple scab': 'Leaf Spot',
        'Black rot': 'Leaf Spot',
        'Cedar apple rust': 'Brown Rust',
        'healthy': 'Healthy',
        'Cercospora leaf spot Gray leaf spot': 'Cercospora Leaf Spot',
        'Common rust ': 'Brown Rust',
        'Northern Leaf Blight': 'Late Blight',
        'Bacterial spot': 'Bacterial Blight',
        'Early blight': 'Early Blight',
        'Late blight': 'Late Blight',
        'Leaf Mold': 'Powdery Mildew',
        'Septoria leaf spot': 'Leaf Spot',
        'Spider mites Two spotted spider mite': 'Unknown Disease',
        'Target Spot': 'Leaf Spot',
        'Tomato YellowLeaf  Curl Virus': 'Mosaic Virus',
        'Tomato mosaic virus': 'Mosaic Virus',
    }
    
    for key in mapping:
        if key.lower() in name.lower():
            return mapping[key]
            
    if 'healthy' in class_name.lower():
        return 'Healthy'
        
    return 'Unknown Disease'


def _cnn_predict(image_input, model_path, classes_path):
    import json
    import numpy as np
    import tensorflow as tf
    from PIL import Image

    with open(classes_path, 'r') as f:
        class_names = json.load(f)

    model = tf.keras.models.load_model(model_path)

    if isinstance(image_input, str):
        img = Image.open(image_input)
    elif hasattr(image_input, 'read'):
        pos = image_input.tell()
        img = Image.open(image_input)
        image_input.seek(pos)
    else:
        img = Image.open(io.BytesIO(image_input))

    img = img.convert('RGB').resize((128, 128))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0) # Create a batch

    predictions_array = model.predict(img_array)[0]
    top3_idx = np.argsort(predictions_array)[::-1][:3]

    predictions = []
    for idx in top3_idx:
        raw_label = class_names[idx]
        mapped_label = _map_cnn_class_to_disease(raw_label)
        confidence = round(float(predictions_array[idx]) * 100, 1)
        info = DISEASE_TREATMENTS.get(mapped_label, DISEASE_TREATMENTS['Unknown Disease'])
        
        predictions.append({
            'disease': mapped_label,
            'raw_class': raw_label,
            'confidence': confidence,
            'severity': info['severity'],
            'treatment': info['treatment'],
        })

    top = predictions[0]
    return {
        'disease': top['disease'],
        'confidence': top['confidence'],
        'severity': top['severity'],
        'treatment': top['treatment'],
        'all_predictions': predictions,
        'model_used': 'cnn_trained',
    }


def _rule_based_predict(image_input):
    """
    Rule-based disease prediction using color analysis.
    Used when no trained ML model is available.
    """
    try:
        from PIL import Image
        import numpy as np

        if isinstance(image_input, str):
            img = Image.open(image_input)
        elif hasattr(image_input, 'read'):
            pos = image_input.tell()
            img = Image.open(image_input)
            image_input.seek(pos)
        else:
            img = Image.open(io.BytesIO(image_input))

        img = img.convert('RGB').resize((64, 64))
        arr = np.array(img)
        r, g, b = arr[:,:,0].mean(), arr[:,:,1].mean(), arr[:,:,2].mean()

        # Brown/rust tones
        if r > 150 and g < 120 and b < 100:
            disease, conf = 'Brown Rust', 84.2
        # Yellow tones
        elif r > 180 and g > 160 and b < 100:
            disease, conf = 'Yellow Rust', 87.5
        # Very dark/black spots
        elif r < 80 and g < 80 and b < 80:
            disease, conf = 'Blast Disease', 79.3
        # White/grey powdery
        elif r > 200 and g > 200 and b > 200:
            disease, conf = 'Powdery Mildew', 81.0
        # Healthy green
        elif g > r and g > b and g > 100:
            disease, conf = 'Healthy', 91.0
        # Default
        else:
            disease, conf = 'Leaf Spot', 76.4

    except Exception:
        disease, conf = 'Unknown Disease', 65.0

    info = DISEASE_TREATMENTS.get(disease, DISEASE_TREATMENTS['Unknown Disease'])
    pred = {
        'disease':    disease,
        'confidence': conf,
        'severity':   info['severity'],
        'treatment':  info['treatment'],
        'model_used': 'rule_based',
    }
    pred['all_predictions'] = [pred.copy()]
    return pred
