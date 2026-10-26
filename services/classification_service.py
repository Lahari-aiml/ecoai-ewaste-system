"""
EcoAI Classification Service
Manages model loading, caching, text preprocessing, and ensemble inference between
NLP (TF-IDF + Calibrated Classifier) and Deep Learning (Dense Neural Network).
"""

import os
from pathlib import Path
from model.nlp_model import NLPClassifier, preprocess_text
from model.deeplearning import DeepLearningClassifier
from database.db import query_db
from config import Config

class ClassificationService:
    _instance = None

    def __init__(self, model_dir=None):
        self.model_dir = Path(model_dir) if model_dir else Path(Config.MODEL_DIR)
        self.nlp_classifier = NLPClassifier(model_dir=self.model_dir)
        self.dl_classifier = DeepLearningClassifier(model_dir=self.model_dir)
        self._is_loaded = False

    @classmethod
    def get_instance(cls, model_dir=None):
        """Singleton accessor for efficient in-memory model reuse across requests."""
        if cls._instance is None:
            cls._instance = cls(model_dir=model_dir)
            cls._instance.ensure_models_loaded()
        return cls._instance

    def ensure_models_loaded(self):
        """Loads models into memory once. Auto-trains if missing."""
        if self._is_loaded:
            return

        if not self.nlp_classifier.is_trained() or not self.dl_classifier.is_trained():
            from model.train_model import train_all_models
            print("[*] Model files not found. Auto-training baseline models...")
            train_all_models(model_dir=self.model_dir, verbose=False)

        self.nlp_classifier.load()
        self.dl_classifier.load()
        self._is_loaded = True

    def classify(self, text: str):
        """
        Runs both NLP and Deep Learning classification.
        Returns predicted category, probabilities, confidence scores, and category database ID.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        self.ensure_models_loaded()

        # 1. NLP Prediction
        nlp_res = self.nlp_classifier.predict(text)

        # 2. Deep Learning Prediction (using TF-IDF feature space)
        clean_text = nlp_res['clean_text']
        if clean_text:
            X_vec = self.nlp_classifier.vectorizer.transform([clean_text])
            dl_res = self.dl_classifier.predict_features(X_vec)
        else:
            dl_res = {
                'predicted_category': 'Recycle',
                'confidence': 0.33,
                'probabilities': {'Repair': 0.33, 'Reuse': 0.33, 'Recycle': 0.34}
            }

        # 3. Ensemble calculation: weighted average of probabilities
        combined_probs = {}
        for cat in ['Repair', 'Reuse', 'Recycle']:
            p_nlp = nlp_res['probabilities'].get(cat, 0.0)
            p_dl = dl_res['probabilities'].get(cat, 0.0)
            combined_probs[cat] = round((0.45 * p_nlp) + (0.55 * p_dl), 4)

        # Select winner from ensemble
        best_category = max(combined_probs, key=combined_probs.get)
        confidence = combined_probs[best_category]

        # 4. Lookup category ID in database
        cat_row = query_db("SELECT id, category_name, description, badge_color, icon FROM categories WHERE category_name = ?", (best_category,), one=True)
        cat_id = cat_row['id'] if cat_row else 1

        return {
            'predicted_category': best_category,
            'category_name': best_category,
            'category_id': cat_id,
            'category_meta': cat_row,
            'confidence': confidence,
            'confidence_percentage': round(confidence * 100, 1),
            'probabilities': combined_probs,
            'clean_text': clean_text,
            'nlp_details': nlp_res,
            'dl_details': dl_res,
            'model_used': 'Ensemble (NLP + Deep Learning)'
        }

def get_classifier():
    return ClassificationService.get_instance()
