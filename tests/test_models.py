"""
Unit tests for EcoAI AI/ML and NLP models.
Tests preprocessing, vectorization, individual model inference, and ensemble predictions.
"""

import unittest
from model.nlp_model import clean_text, NLPClassifier
from model.deeplearning import DeepLearningClassifier
from services.classification_service import ClassificationService, get_classifier

class TestEcoAIModels(unittest.TestCase):

    def setUp(self):
        self.nlp = NLPClassifier()
        self.dl = DeepLearningClassifier()
        self.ensemble = get_classifier()

    def test_text_cleaning(self):
        sample = " Broken Samsung Galaxy S10!! Battery won't charge? 123 "
        cleaned = clean_text(sample)
        self.assertNotIn("!", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertEqual(cleaned, cleaned.lower().strip())

    def test_nlp_prediction_repair(self):
        text = "Laptop boots fine but display screen is cracked and flickering"
        pred, conf, probs = self.nlp.predict(text)
        self.assertIn(pred, ['Repair', 'Reuse', 'Recycle'])
        self.assertGreater(conf, 0.0)
        self.assertLessEqual(conf, 1.0)
        self.assertIn('Repair', probs)

    def test_nlp_prediction_recycle(self):
        text = "Completely destroyed melted motherboard with burnt burnt chips and chemical leak"
        pred, conf, probs = self.nlp.predict(text)
        self.assertIn(pred, ['Repair', 'Reuse', 'Recycle'])
        self.assertGreater(conf, 0.0)

    def test_dl_prediction_smoke(self):
        text = "Fully working iPhone in pristine condition, battery health 95%"
        pred, conf, probs = self.dl.predict(text)
        self.assertIn(pred, ['Repair', 'Reuse', 'Recycle'])
        self.assertGreater(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

    def test_ensemble_classification(self):
        text = "Old desktop computer with faulty RAM and blue screen error"
        res = self.ensemble.classify(text)
        self.assertIn('category_name', res)
        self.assertIn(res['category_name'], ['Repair', 'Reuse', 'Recycle'])
        self.assertIn(res['category_id'], [1, 2, 3])
        self.assertGreater(res['confidence'], 0.0)
        self.assertIn('nlp_details', res)
        self.assertIn('dl_details', res)

if __name__ == '__main__':
    unittest.main()
