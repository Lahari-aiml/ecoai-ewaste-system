"""
EcoAI NLP Model Module
Handles text preprocessing, TF-IDF vectorization, and NLP model classification with calibrated probabilities.
"""

import re
import os
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Stop words list (curated standard English stop words)
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'by', 'could', 'did', 'do',
    'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have',
    'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in',
    'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not',
    'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over',
    'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs',
    'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while',
    'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
}

def preprocess_text(text: str) -> str:
    """
    Cleans, normalizes, and tokenizes input text.
    Removes punctuation, numbers, special characters, and common stop words.
    """
    if not text or not isinstance(text, str):
        return ""

    # Convert to lowercase
    text = text.lower().strip()

    # Replace URLs and emails
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)

    # Remove non-alphabetical characters (keep letters and spaces)
    text = re.sub(r'[^a-z\s]', ' ', text)

    # Tokenize by whitespace
    tokens = text.split()

    # Filter stopwords and short tokens
    cleaned_tokens = [tok for tok in tokens if tok not in STOP_WORDS and len(tok) > 1]

    return ' '.join(cleaned_tokens)

# Alias for backwards/test compatibility
clean_text = preprocess_text

class PredictionResult(dict):
    """
    Specialized result dictionary that supports both dict access
    and 3-tuple unpacking: pred, conf, probs = result
    """
    def __iter__(self):
        return iter([self['predicted_category'], self['confidence'], self['probabilities']])

class NLPClassifier:
    """
    NLP Text Classifier using TF-IDF vectorization and Calibrated Logistic Regression.
    Provides realistic class probabilities and top prediction.
    """
    def __init__(self, model_dir=None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent
        self.vectorizer_path = self.model_dir / 'tfidf_vectorizer.pkl'
        self.classifier_path = self.model_dir / 'nlp_classifier.pkl'
        self.vectorizer = None
        self.classifier = None
        self.classes_ = ['Repair', 'Reuse', 'Recycle']

    def is_trained(self) -> bool:
        return self.vectorizer_path.exists() and self.classifier_path.exists()

    def train(self, texts, labels):
        """Train TF-IDF vectorizer and calibrated classifier on preprocessed texts."""
        clean_texts = [preprocess_text(t) for t in texts]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=3000,
            sublinear_tf=True
        )
        X = self.vectorizer.fit_transform(clean_texts)

        base_lr = LogisticRegression(max_iter=500, C=1.5, class_weight='balanced', random_state=42)
        self.classifier = base_lr
        self.classifier.fit(X, labels)
        self.classes_ = list(self.classifier.classes_)

        # Save artifacts
        self.save()
        return self

    def save(self):
        """Save vectorizer and classifier to disk."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.classifier, self.classifier_path)

    def load(self):
        """Load vectorizer and classifier from disk."""
        if not self.is_trained():
            raise FileNotFoundError(f"Model artifacts not found in {self.model_dir}. Please run train_model.py first.")
        self.vectorizer = joblib.load(self.vectorizer_path)
        self.classifier = joblib.load(self.classifier_path)
        self.classes_ = list(self.classifier.classes_)
        return self

    def predict(self, raw_text: str):
        """
        Predict category for raw text.
        Returns PredictionResult supporting dict access and 3-tuple unpacking.
        """
        if self.vectorizer is None or self.classifier is None:
            self.load()

        clean_t = preprocess_text(raw_text)
        if not clean_t:
            return PredictionResult({
                'predicted_category': 'Recycle',
                'confidence': 0.33,
                'probabilities': {'Repair': 0.33, 'Reuse': 0.33, 'Recycle': 0.34},
                'clean_text': ''
            })

        X = self.vectorizer.transform([clean_t])
        probs = self.classifier.predict_proba(X)[0]
        class_probs = {cls: round(float(p), 4) for cls, p in zip(self.classes_, probs)}

        best_idx = probs.argmax()
        predicted_cat = self.classes_[best_idx]
        confidence = round(float(probs[best_idx]), 4)

        return PredictionResult({
            'predicted_category': predicted_cat,
            'confidence': confidence,
            'probabilities': class_probs,
            'clean_text': clean_t
        })
