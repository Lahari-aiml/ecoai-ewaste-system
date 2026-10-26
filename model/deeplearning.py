"""
EcoAI Deep Learning Model Module
Implements a Deep Neural Network (Multi-Layer Perceptron architecture)
with Dense layers, ReLU activations, Adam optimization, and Softmax probability distribution.
"""

import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from model.nlp_model import preprocess_text, PredictionResult, NLPClassifier

class DeepLearningClassifier:
    """
    Deep Neural Network classifier for e-waste categorization.
    Architecture:
      Input (TF-IDF Feature Space, ~3000 dim)
      -> Dense Layer 1 (128 units, ReLU activation)
      -> Dense Layer 2 (64 units, ReLU activation)
      -> Softmax Output Layer (3 units: Repair, Reuse, Recycle)
    """
    def __init__(self, model_dir=None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent
        self.model_path = self.model_dir / 'dl_classifier.pkl'
        self.model = None
        self.classes_ = ['Repair', 'Reuse', 'Recycle']
        self._nlp_helper = None

    def is_trained(self) -> bool:
        return self.model_path.exists()

    def train(self, X_features, labels):
        """
        Train the Deep Neural Network on TF-IDF features and target labels.
        """
        self.model = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size=16,
            learning_rate_init=0.001,
            max_iter=400,
            random_state=42,
            early_stopping=True,
            n_iter_no_change=15,
            validation_fraction=0.1
        )
        self.model.fit(X_features, labels)
        self.classes_ = list(self.model.classes_)
        self.save()
        return self

    def save(self):
        """Save neural network weights and architecture to disk."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def load(self):
        """Load trained neural network model from disk."""
        if not self.is_trained():
            raise FileNotFoundError(f"Deep learning model not found at {self.model_path}. Please train first.")
        self.model = joblib.load(self.model_path)
        self.classes_ = list(self.model.classes_)
        return self

    def predict_features(self, X_features):
        """
        Predict category and probabilities from TF-IDF feature matrix.
        """
        if self.model is None:
            self.load()

        probs = self.model.predict_proba(X_features)[0]
        class_probs = {cls: round(float(p), 4) for cls, p in zip(self.classes_, probs)}

        best_idx = probs.argmax()
        predicted_cat = self.classes_[best_idx]
        confidence = round(float(probs[best_idx]), 4)

        return PredictionResult({
            'predicted_category': predicted_cat,
            'confidence': confidence,
            'probabilities': class_probs
        })

    def predict(self, raw_text: str):
        """
        Predict category for raw text using the NLP TF-IDF vectorizer.
        Returns PredictionResult supporting dict access and 3-tuple unpacking.
        """
        if self.model is None:
            self.load()

        if self._nlp_helper is None:
            self._nlp_helper = NLPClassifier(model_dir=self.model_dir)
            self._nlp_helper.load()

        clean_t = preprocess_text(raw_text)
        if not clean_t:
            return PredictionResult({
                'predicted_category': 'Recycle',
                'confidence': 0.33,
                'probabilities': {'Repair': 0.33, 'Reuse': 0.33, 'Recycle': 0.34}
            })

        X_vec = self._nlp_helper.vectorizer.transform([clean_t])
        return self.predict_features(X_vec)
