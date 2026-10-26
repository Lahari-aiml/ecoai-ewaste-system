"""
EcoAI Model Training Script
Trains both the NLP Classifier (TF-IDF + Calibrated Model) and the Deep Neural Network.
Evaluates accuracy, generates performance reports, and serializes trained artifacts.
"""

import os
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from model.dataset import DATASET
from model.nlp_model import NLPClassifier, preprocess_text
from model.deeplearning import DeepLearningClassifier

def train_all_models(model_dir=None, verbose=True):
    """
    Train and serialize both NLP and Deep Learning models on the EcoAI dataset.
    """
    target_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent

    if verbose:
        print("=" * 60)
        print("  EcoAI Machine Learning & Deep Learning Training Pipeline")
        print("=" * 60)
        print(f"[*] Dataset total samples: {len(DATASET)}")

    texts = [item[0] for item in DATASET]
    labels = [item[1] for item in DATASET]

    # Stratified train-test split (80% train, 20% test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    if verbose:
        print(f"[*] Training samples: {len(X_train_raw)} | Testing samples: {len(X_test_raw)}")
        print("\n--- Training NLP Model (TF-IDF + Calibrated Classifier) ---")

    # 1. Train NLP Model
    nlp = NLPClassifier(model_dir=target_dir)
    nlp.train(X_train_raw, y_train)

    # Evaluate NLP Model
    y_pred_nlp = [nlp.predict(t)['predicted_category'] for t in X_test_raw]
    nlp_acc = accuracy_score(y_test, y_pred_nlp)

    if verbose:
        print(f"[+] NLP Model Test Accuracy: {nlp_acc * 100:.2f}%")
        print("NLP Classification Report:")
        print(classification_report(y_test, y_pred_nlp, digits=3))

    # 2. Train Deep Learning Neural Network
    if verbose:
        print("\n--- Training Deep Learning Model (Dense Neural Network) ---")

    dl = DeepLearningClassifier(model_dir=target_dir)

    # Preprocess & vectorise training features using the trained TF-IDF vectorizer
    clean_train = [preprocess_text(t) for t in X_train_raw]
    X_train_vec = nlp.vectorizer.transform(clean_train)

    clean_test = [preprocess_text(t) for t in X_test_raw]
    X_test_vec = nlp.vectorizer.transform(clean_test)

    dl.train(X_train_vec, y_train)

    # Evaluate Deep Learning Model
    y_pred_dl = []
    for i in range(X_test_vec.shape[0]):
        row_feat = X_test_vec[i:i+1]
        res = dl.predict_features(row_feat)
        y_pred_dl.append(res['predicted_category'])

    dl_acc = accuracy_score(y_test, y_pred_dl)

    if verbose:
        print(f"[+] Deep Learning Model Test Accuracy: {dl_acc * 100:.2f}%")
        print("Deep Learning Classification Report:")
        print(classification_report(y_test, y_pred_dl, digits=3))
        print(f"\n[*] Artifacts saved to: {target_dir}")
        print("    - tfidf_vectorizer.pkl")
        print("    - nlp_classifier.pkl")
        print("    - dl_classifier.pkl")
        print("=" * 60)

    return {
        'nlp_accuracy': nlp_acc,
        'dl_accuracy': dl_acc,
        'test_count': len(y_test)
    }

if __name__ == '__main__':
    train_all_models()
