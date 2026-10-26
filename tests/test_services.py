"""
Unit tests for EcoAI core business services.
Tests Haversine distance, city coordinates, provider search, recommendations, and pickups.
"""

import unittest
import os
import shutil
from pathlib import Path

from config import Config
from database.seed import seed_database
from database.db import query_db, get_db
from services.location_service import haversine, get_city_coordinates, find_nearby_providers
from services.recommendation_service import get_recommendation_by_category, update_recommendation
from services.pickup_service import create_pickup_request, cancel_user_pickup, update_pickup_status, get_user_pickups

TEST_DB = str(Path(__file__).resolve().parent / 'test_services.db')

class TestEcoAIServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['ECOAI_DATABASE'] = TEST_DB
        seed_database(TEST_DB)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass

    def test_haversine_same_point(self):
        # Distance between identical points is 0
        dist = haversine(12.9716, 77.5946, 12.9716, 77.5946)
        self.assertEqual(dist, 0.0)

    def test_haversine_known_distance(self):
        # Distance between Bengaluru (12.9716, 77.5946) and Hyderabad (17.3850, 78.4867) is approx 500 km
        dist = haversine(12.9716, 77.5946, 17.3850, 78.4867)
        self.assertGreater(dist, 480.0)
        self.assertLess(dist, 520.0)

    def test_city_coordinates_lookup(self):
        bengaluru = get_city_coordinates('bengaluru')
        self.assertIsNotNone(bengaluru)
        self.assertAlmostEqual(bengaluru['lat'], 12.9716, places=2)

        delhi = get_city_coordinates('Delhi')
        self.assertIsNotNone(delhi)
        self.assertAlmostEqual(delhi['lat'], 28.6139, places=2)

        invalid = get_city_coordinates('NonExistentCityXYZ')
        self.assertIsNone(invalid)

    def test_find_nearby_providers_default_radius(self):
        # Bengaluru center search
        res = find_nearby_providers(12.9716, 77.5946, radius_km=25.0)
        self.assertIn('providers', res)
        self.assertGreater(len(res['providers']), 0)
        # Providers should be sorted by distance
        distances = [p['distance_km'] for p in res['providers'] if p['distance_km'] is not None]
        self.assertEqual(distances, sorted(distances))

    def test_find_nearby_providers_category_filter(self):
        # Category 1 = Repair
        res = find_nearby_providers(12.9716, 77.5946, category_id=1, radius_km=50.0)
        for p in res['providers']:
            self.assertEqual(p['category_id'], 1)

    def test_recommendation_fetch_and_update(self):
        rec = get_recommendation_by_category(1, db_path=TEST_DB)
        self.assertIsNotNone(rec)
        self.assertEqual(rec['category_name'], 'Repair')
        self.assertIn('safety_guidelines', rec)

        # Update recommendation
        update_recommendation(
            category_id=1,
            recommendation_text="Updated Repair Recommendation Advice",
            instructions="Updated step 1 2 3",
            safety_guidelines="Handle with insulated gloves",
            db_path=TEST_DB
        )
        updated_rec = get_recommendation_by_category(1, db_path=TEST_DB)
        self.assertEqual(updated_rec['recommendation_text'], "Updated Repair Recommendation Advice")

    def test_pickup_lifecycle(self):
        # Get demo user and provider
        user = query_db("SELECT id FROM users WHERE role = 'user' LIMIT 1", one=True, db_path=TEST_DB)
        provider = query_db("SELECT id FROM service_providers WHERE offers_pickup = 1 LIMIT 1", one=True, db_path=TEST_DB)
        self.assertIsNotNone(user)
        self.assertIsNotNone(provider)

        # 1. Create pickup request
        req_id = create_pickup_request(
            user_id=user['id'],
            provider_id=provider['id'],
            address="123 Tech Park Road, Bengaluru",
            phone="+91 98765 43210",
            preferred_date="2026-12-01",
            instructions="Fragile LCD panel",
            db_path=TEST_DB
        )
        self.assertIsInstance(req_id, int)

        # 2. Verify in user pickups
        user_pickups = get_user_pickups(user['id'], db_path=TEST_DB)
        req_entry = next((p for p in user_pickups if p['id'] == req_id), None)
        self.assertIsNotNone(req_entry)
        self.assertEqual(req_entry['status'], 'Pending')

        # 3. Update status (Confirmed -> Picked Up -> Completed)
        update_pickup_status(req_id, 'Confirmed', notes="Pickup scheduled for morning", db_path=TEST_DB)
        row = query_db("SELECT status, notes FROM pickup_requests WHERE id = ?", (req_id,), one=True, db_path=TEST_DB)
        self.assertEqual(row['status'], 'Confirmed')
        self.assertEqual(row['notes'], "Pickup scheduled for morning")

        # 4. Cancel pickup test
        new_req_id = create_pickup_request(
            user_id=user['id'],
            provider_id=provider['id'],
            address="456 Green Street, Bengaluru",
            phone="+91 98765 43210",
            preferred_date="2026-12-02",
            db_path=TEST_DB
        )
        cancel_user_pickup(new_req_id, user['id'], db_path=TEST_DB)
        cancelled_row = query_db("SELECT status FROM pickup_requests WHERE id = ?", (new_req_id,), one=True, db_path=TEST_DB)
        self.assertEqual(cancelled_row['status'], 'Cancelled')

if __name__ == '__main__':
    unittest.main()
