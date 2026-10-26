"""
EcoAI Comprehensive Test Suite
Validates core functional requirements, security boundaries, model inferences,
location calculations, and database isolation across all 13 required test scenarios.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from database.db import get_db, init_db, query_db, execute_db
from database.seed import seed_database
from services.location_service import haversine, find_nearby_providers
from services.recommendation_service import get_recommendation_by_category
from services.classification_service import get_classifier
from config import Config

class EcoAITestCase(unittest.TestCase):
    def setUp(self):
        """Set up fresh test application with an isolated test database."""
        self.test_db_path = str(ROOT_DIR / 'database' / 'ecoai_test.db')
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

        self.app = create_app('testing')
        self.app.config['DATABASE'] = self.test_db_path
        self.client = self.app.test_client()

        with self.app.app_context():
            seed_database(self.test_db_path)

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    # Helper: Register a new user
    def register_user(self, name="Test Citizen", email="test@example.com", username="testuser", password="Password123"):
        return self.client.post('/signup', data={
            'name': name,
            'email': email,
            'username': username,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

    # Helper: Sign in
    def login_user(self, username_or_email="testuser", password="Password123"):
        return self.client.post('/login', data={
            'username_or_email': username_or_email,
            'password': password
        }, follow_redirects=True)

    # Helper: Sign in admin
    def login_admin(self, username="admin", password="Admin@EcoAI2026"):
        return self.client.post('/admin/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    # --------------------------------------------------------------------------
    # Test 1: User registration and login
    # --------------------------------------------------------------------------
    def test_01_user_registration_and_login(self):
        # Register
        resp = self.register_user("Alice Green", "alice@test.com", "alice", "Secret123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Hello, Alice Green', resp.data)

        # Logout
        self.client.get('/logout')

        # Login
        resp_login = self.login_user("alice", "Secret123")
        self.assertEqual(resp_login.status_code, 200)
        self.assertIn(b'Hello, Alice Green', resp_login.data)

    # --------------------------------------------------------------------------
    # Test 2: Duplicate account validation
    # --------------------------------------------------------------------------
    def test_02_duplicate_account_validation(self):
        self.register_user("User One", "user1@test.com", "user1", "Secret123")
        self.client.get('/logout')

        # Duplicate username
        resp_dup_user = self.register_user("User Two", "user2@test.com", "user1", "Secret123")
        self.assertIn(b'username is already taken', resp_dup_user.data)

        # Duplicate email
        resp_dup_email = self.register_user("User Three", "user1@test.com", "user3", "Secret123")
        self.assertIn(b'email address already exists', resp_dup_email.data)

    # --------------------------------------------------------------------------
    # Test 3: Accessing protected pages without logging in
    # --------------------------------------------------------------------------
    def test_03_access_protected_pages_without_login(self):
        protected_urls = ['/dashboard', '/history', '/my-pickups']
        for url in protected_urls:
            resp = self.client.get(url, follow_redirects=True)
            self.assertIn(b'Please sign in to access this page', resp.data)
            self.assertIn(b'Sign In', resp.data)

    # --------------------------------------------------------------------------
    # Test 4: User and admin permission separation
    # --------------------------------------------------------------------------
    def test_04_user_admin_permission_separation(self):
        # Regular user tries to access /admin/dashboard
        self.register_user("Regular User", "regular@test.com", "regular", "Secret123")
        resp = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Administrator privileges are required', resp.data)

        # Logout and sign in as actual Admin
        self.client.get('/logout')
        admin_resp = self.login_admin("admin", "Admin@EcoAI2026")
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIn(b'System Administration', admin_resp.data)

    # --------------------------------------------------------------------------
    # Test 5: Classification with valid text
    # --------------------------------------------------------------------------
    def test_05_classification_with_valid_text(self):
        self.register_user()

        # Classify a cracked screen laptop (should be Repair)
        resp = self.client.post('/classify/predict', data={
            'description': 'My old laptop switches on, but its screen is damaged and cracked.'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Repair', resp.data)
        self.assertIn(b'AI Classification Outcome', resp.data)
        self.assertIn(b'Actionable Instructions', resp.data)

    # --------------------------------------------------------------------------
    # Test 6: Classification with empty input
    # --------------------------------------------------------------------------
    def test_06_classification_with_empty_input(self):
        self.register_user()
        resp = self.client.post('/classify/predict', data={'description': '   '}, follow_redirects=True)
        self.assertIn(b'Please enter a description', resp.data)

    # --------------------------------------------------------------------------
    # Test 7: Recommendation retrieval
    # --------------------------------------------------------------------------
    def test_07_recommendation_retrieval(self):
        with self.app.app_context():
            rec_repair = get_recommendation_by_category('Repair')
            self.assertIsNotNone(rec_repair)
            self.assertEqual(rec_repair['category_name'], 'Repair')
            self.assertTrue(len(rec_repair['steps']) > 0)

            rec_recycle = get_recommendation_by_category(3)
            self.assertIsNotNone(rec_recycle)
            self.assertEqual(rec_recycle['category_name'], 'Recycle')
            self.assertIn('lead', rec_recycle['safety_guidelines'].lower())

    # --------------------------------------------------------------------------
    # Test 8: Nearby-provider filtering and distance calculation
    # --------------------------------------------------------------------------
    def test_08_nearby_provider_filtering_and_distance(self):
        # Indiranagar Bengaluru (~12.9784, 77.6408) to Peenya (~13.0334, 77.5140)
        dist = haversine(12.9784, 77.6408, 13.0334, 77.5140)
        self.assertTrue(10.0 <= dist <= 20.0, f"Calculated distance {dist} km is out of expected range")

        with self.app.app_context():
            res = find_nearby_providers(
                user_lat=12.9784, user_lon=77.6408, category_id=1, radius_km=25.0, limit=5
            )
            self.assertTrue(len(res['providers']) > 0)
            for p in res['providers']:
                self.assertEqual(p['category_name'], 'Repair')
                self.assertLessEqual(p['distance_km'], 25.0)

    # --------------------------------------------------------------------------
    # Test 9: Provider search when no location is available
    # --------------------------------------------------------------------------
    def test_09_provider_search_city_fallback(self):
        # Search using city fallback 'delhi'
        resp = self.client.get('/providers?city=delhi&radius=25', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Nehru Place Hardware Repair', resp.data)

    # --------------------------------------------------------------------------
    # Test 10: Pickup request submission
    # --------------------------------------------------------------------------
    def test_10_pickup_request_submission(self):
        self.register_user()

        with self.app.app_context():
            provider = query_db("SELECT id FROM service_providers WHERE offers_pickup = 1 LIMIT 1", one=True)
            provider_id = provider['id']

        resp = self.client.post('/pickup/submit', data={
            'provider_id': provider_id,
            'address': 'Flat 204, Green Heights, Indiranagar, Bengaluru',
            'phone': '9845099887',
            'preferred_date': '2026-11-20',
            'instructions': 'Please call 10 mins before arrival'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Doorstep pickup request scheduled successfully', resp.data)
        self.assertIn(b'Pending', resp.data)

    # --------------------------------------------------------------------------
    # Test 11: Pickup request cancellation and status updates
    # --------------------------------------------------------------------------
    def test_11_pickup_cancellation_and_status_transitions(self):
        self.register_user()

        # Submit request
        with self.app.app_context():
            provider = query_db("SELECT id FROM service_providers WHERE offers_pickup = 1 LIMIT 1", one=True)
            provider_id = provider['id']

        self.client.post('/pickup/submit', data={
            'provider_id': provider_id,
            'address': 'Test Address 123',
            'phone': '9845012345',
            'preferred_date': '2026-11-25'
        }, follow_redirects=True)

        with self.app.app_context():
            req = query_db("SELECT id, status FROM pickup_requests ORDER BY id DESC LIMIT 1", one=True)
            req_id = req['id']
            self.assertEqual(req['status'], 'Pending')

        # Cancel request as user
        resp_cancel = self.client.post(f'/pickup/cancel/{req_id}', follow_redirects=True)
        self.assertIn(b'Your pickup request has been cancelled', resp_cancel.data)

        with self.app.app_context():
            updated_req = query_db("SELECT status FROM pickup_requests WHERE id = ?", (req_id,), one=True)
            self.assertEqual(updated_req['status'], 'Cancelled')

    # --------------------------------------------------------------------------
    # Test 12: User isolation for prediction history and pickup requests
    # --------------------------------------------------------------------------
    def test_12_user_isolation(self):
        # User 1 registers and creates a prediction
        self.register_user("User Alpha", "alpha@test.com", "alpha", "Pass123")
        self.client.post('/classify/predict', data={'description': 'Alpha private old laptop screen broken'}, follow_redirects=True)

        with self.app.app_context():
            alpha_pred = query_db("SELECT id FROM predictions ORDER BY id DESC LIMIT 1", one=True)
            alpha_pred_id = alpha_pred['id']

        # User 1 logs out
        self.client.get('/logout')

        # User 2 registers
        self.register_user("User Beta", "beta@test.com", "beta", "Pass123")

        # User 2 checks history (should NOT see Alpha's item)
        resp_history = self.client.get('/history')
        self.assertNotIn(b'Alpha private old laptop', resp_history.data)

        # User 2 tries to view User 1's prediction result directly
        resp_view = self.client.get(f'/result/{alpha_pred_id}', follow_redirects=True)
        self.assertIn(b'do not have permission to view that prediction', resp_view.data)

    # --------------------------------------------------------------------------
    # Test 13: Admin CRUD operations
    # --------------------------------------------------------------------------
    def test_13_admin_crud_operations(self):
        # Login admin
        self.login_admin()

        # 1. Add Provider
        resp_add = self.client.post('/admin/providers/add', data={
            'name': 'Test Apex Recovery Hub',
            'category_id': 3,
            'phone': '+91 99999 88888',
            'email': 'apex@test.demo',
            'address': 'Plot 100 Tech Park',
            'city': 'Bengaluru',
            'latitude': '12.9900',
            'longitude': '77.6600',
            'offers_pickup': '1',
            'verification_status': 'Verified'
        }, follow_redirects=True)
        self.assertIn(b'Test Apex Recovery Hub', resp_add.data)

        with self.app.app_context():
            p_row = query_db("SELECT id, is_active FROM service_providers WHERE name = 'Test Apex Recovery Hub'", one=True)
            self.assertIsNotNone(p_row)
            p_id = p_row['id']

        # 2. Toggle Provider status
        self.client.post(f'/admin/providers/toggle/{p_id}', follow_redirects=True)
        with self.app.app_context():
            p_toggled = query_db("SELECT is_active FROM service_providers WHERE id = ?", (p_id,), one=True)
            self.assertEqual(p_toggled['is_active'], 0)

        # 3. Update Category Recommendation
        resp_cat = self.client.post('/admin/categories/update/1', data={
            'cat_description': 'Updated repair description',
            'recommendation_text': 'Updated repair recommendation text',
            'instructions': 'Step 1: Check power\nStep 2: Check screen',
            'safety_guidelines': 'Safety first!'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', resp_cat.data)

        # 4. Delete Provider
        self.client.post(f'/admin/providers/delete/{p_id}', follow_redirects=True)
        with self.app.app_context():
            p_deleted = query_db("SELECT id FROM service_providers WHERE id = ?", (p_id,), one=True)
            self.assertIsNone(p_deleted)

if __name__ == '__main__':
    unittest.main()
