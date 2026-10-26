"""
Integration tests for EcoAI Flask application routes and controllers.
Covers authentication, authorization, AI prediction, maps, pickups, and admin management.
"""

import unittest
import os
from pathlib import Path

from app import create_app
from database.seed import seed_database
from database.db import query_db, execute_db

TEST_DB = str(Path(__file__).resolve().parent / 'test_routes.db')

class TestEcoAIRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['ECOAI_DATABASE'] = TEST_DB
        seed_database(TEST_DB)
        cls.app = create_app('testing')
        cls.app.config['DATABASE'] = TEST_DB
        cls.app.config['WTF_CSRF_ENABLED'] = False

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass

    def setUp(self):
        self.client = self.app.test_client()

    def login_as_user(self):
        """Helper to login as demo user."""
        return self.client.post('/login', data={
            'username_or_email': 'demo_user',
            'password': 'User@EcoAI2026'
        }, follow_redirects=True)

    def login_as_admin(self):
        """Helper to login as demo admin."""
        return self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'Admin@EcoAI2026'
        }, follow_redirects=True)

    # --------------------------------------------------------------------------
    # Public Routes Tests
    # --------------------------------------------------------------------------
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'EcoAI', response.data)
        self.assertIn(b'Intelligent E-Waste Management', response.data)

    def test_classify_page_get(self):
        response = self.client.get('/classify')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI E-Waste Classifier', response.data)

    def test_providers_page_public(self):
        response = self.client.get('/providers?city=bengaluru&radius=25')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Nearby Service Providers', response.data)
        self.assertIn(b'id="map"', response.data)
        self.assertIn(b'id="providers-data"', response.data)

    # --------------------------------------------------------------------------
    # Authentication Tests
    # --------------------------------------------------------------------------
    def test_signup_flow(self):
        res = self.client.post('/signup', data={
            'name': 'Test Newbie',
            'email': 'newbie@example.com',
            'username': 'newbie2026',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome to your personal e-waste circular disposition dashboard', res.data)

        # Cleanup
        with self.app.app_context():
            execute_db("DELETE FROM users WHERE username = 'newbie2026'")

    def test_login_invalid_credentials(self):
        res = self.client.post('/login', data={
            'username_or_email': 'demo_user',
            'password': 'WrongPasswordXYZ'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Invalid username/email or password', res.data)

    def test_protected_dashboard_redirects_unauthenticated(self):
        res = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    # --------------------------------------------------------------------------
    # Prediction Flow Tests
    # --------------------------------------------------------------------------
    def test_predict_and_view_result(self):
        self.login_as_user()

        # Submit prediction
        res = self.client.post('/classify/predict', data={
            'description': 'Laptop boots with broken cracked LCD screen and battery charges normally'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI Classification Outcome', res.data)
        self.assertIn(b'Confidence', res.data)

    # --------------------------------------------------------------------------
    # Pickup Flow Tests
    # --------------------------------------------------------------------------
    def test_pickup_schedule_and_listing(self):
        self.login_as_user()

        # Get first provider that offers pickup
        with self.app.app_context():
            provider = query_db("SELECT id FROM service_providers WHERE offers_pickup = 1 LIMIT 1", one=True)

        res = self.client.post('/pickup/submit', data={
            'provider_id': str(provider['id']),
            'address': 'Flat 402, Green Meadows, Bengaluru',
            'phone': '+91 9988776655',
            'preferred_date': '2026-11-20',
            'instructions': 'Please call before arrival'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Doorstep Pickup Requests', res.data)
        self.assertIn(b'Pending', res.data)

    # --------------------------------------------------------------------------
    # Admin Panel Tests
    # --------------------------------------------------------------------------
    def test_admin_dashboard_protected_from_regular_users(self):
        self.login_as_user()
        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/login', res.headers['Location'])

    def test_admin_dashboard_access_for_admin(self):
        self.login_as_admin()
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Admin Control Panel', res.data)
        self.assertIn(b'System Administration', res.data)

    def test_admin_providers_management(self):
        self.login_as_admin()
        res = self.client.get('/admin/providers')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Service Provider Directory', res.data)

    def test_admin_categories_view(self):
        self.login_as_admin()
        res = self.client.get('/admin/categories')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Three-Tier Circular Economy Structure', res.data)

    def test_admin_pickups_view(self):
        self.login_as_admin()
        res = self.client.get('/admin/pickups')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Pickup Request Dispatch & Logistics', res.data)

if __name__ == '__main__':
    unittest.main()
