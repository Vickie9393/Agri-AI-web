import os
import json
import logging
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import layers, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = BASE_DIR / 'Dataset'
MODEL_SAVE_PATH = BASE_DIR / 'agriai_app' / 'ml' / 'cnn_disease_model.keras'
CLASSES_SAVE_PATH = BASE_DIR / 'agriai_app' / 'ml' / 'cnn_classes.json'

# Image parameters
IMG_HEIGHT = 128
IMG_WIDTH = 128
BATCH_SIZE = 32
EPOCHS = 10 # Change as needed for better accuracy

def build_model(num_classes):
    model = models.Sequential([
        layers.Rescaling(1./255, input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D(2, 2),
        
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model

def train():
    if not DATASET_DIR.exists():
        logger.error(f"Dataset directory not found at {DATASET_DIR}")
        return

    logger.info("Loading dataset...")
    
    # Load dataset
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE
    )
    
    class_names = train_ds.class_names
    num_classes = len(class_names)
    logger.info(f"Found {num_classes} classes: {class_names}")
    
    # Cache and prefetch for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    
    logger.info("Building model...")
    model = build_model(num_classes)
    model.summary()
    
    logger.info(f"Training for {EPOCHS} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS
    )
    
    logger.info("Training complete. Saving model...")
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    model.save(MODEL_SAVE_PATH)
    logger.info(f"Model saved to {MODEL_SAVE_PATH}")
    
    # Save classes
    with open(CLASSES_SAVE_PATH, 'w') as f:
        json.dump(class_names, f)
    logger.info(f"Classes saved to {CLASSES_SAVE_PATH}")

if __name__ == "__main__":
    train()
