"""
EcoAI – Intelligent E-Waste Management System
Main Flask Application Controller
"""

import os
import re
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort

from config import Config, config_by_name
from database.db import get_db, close_db, query_db, execute_db, init_db
from database.seed import seed_database
from services.classification_service import get_classifier
from services.recommendation_service import get_recommendation_by_category, update_recommendation
from services.location_service import find_nearby_providers, get_city_coordinates
from services.pickup_service import (
    create_pickup_request, cancel_user_pickup, update_pickup_status,
    get_user_pickups, get_all_pickups
)
from werkzeug.security import generate_password_hash, check_password_hash

def create_app(config_name=None):
    """Application factory for Flask app."""
    app = Flask(__name__)
    cfg_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config_by_name.get(cfg_name, Config))

    # Register teardown
    app.teardown_appcontext(close_db)

    # Auto-initialize and seed database if not present
    with app.app_context():
        db_path = app.config['DATABASE']
        if not os.path.exists(db_path):
            print(f"[*] Initializing and seeding database at {db_path}...")
            seed_database(db_path)

    # --------------------------------------------------------------------------
    # Authentication & Authorization Decorators
    # --------------------------------------------------------------------------
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please sign in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('user_role') != 'admin':
                flash('Administrator privileges are required to view this area.', 'danger')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function

    # --------------------------------------------------------------------------
    # Public Routes: Landing Page
    # --------------------------------------------------------------------------
    @app.route('/')
    def index():
        # Live stats from SQLite database
        total_predictions = query_db("SELECT COUNT(*) FROM predictions", one=True)['COUNT(*)']
        total_providers = query_db("SELECT COUNT(*) FROM service_providers WHERE is_active = 1", one=True)['COUNT(*)']
        total_users = query_db("SELECT COUNT(*) FROM users WHERE role = 'user'", one=True)['COUNT(*)']
        completed_pickups = query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Completed'", one=True)['COUNT(*)']

        stats = {
            'total_predictions': total_predictions,
            'total_providers': total_providers,
            'total_users': total_users,
            'completed_pickups': completed_pickups
        }
        return render_template('index.html', stats=stats)

    # --------------------------------------------------------------------------
    # User Registration & Authentication Routes
    # --------------------------------------------------------------------------
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Server-side validation
            if not name or not email or not username or not password:
                flash('All fields are required.', 'danger')
                return render_template('signup.html')

            if len(username) < 3:
                flash('Username must be at least 3 characters long.', 'danger')
                return render_template('signup.html')

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Please enter a valid email address.', 'danger')
                return render_template('signup.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('signup.html')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('signup.html')

            # Check for existing username or email
            existing_user = query_db(
                "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
                (username, email), one=True
            )
            if existing_user:
                if existing_user['username'] == username:
                    flash('That username is already taken. Please choose another.', 'danger')
                else:
                    flash('An account with this email address already exists.', 'danger')
                return render_template('signup.html')

            # Hash password securely
            pw_hash = generate_password_hash(password)

            # Insert new user with strict 'user' role (cannot elevate via form)
            user_id, _ = execute_db("""
                INSERT INTO users (name, email, username, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, 'user', 1)
            """, (name, email, username, pw_hash))

            # Auto-login after registration
            session.clear()
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_role'] = 'user'

            flash(f'Account created successfully! Welcome to EcoAI, {name}.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            if session.get('user_role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username_or_email = request.form.get('username_or_email', '').strip().lower()
            password = request.form.get('password', '')

            if not username_or_email or not password:
                flash('Please provide both username/email and password.', 'danger')
                return render_template('login.html')

            user = query_db("""
                SELECT id, name, email, username, password_hash, role, is_active
                FROM users
                WHERE (LOWER(username) = ? OR LOWER(email) = ?)
            """, (username_or_email, username_or_email), one=True)

            if not user or not check_password_hash(user['password_hash'], password):
                flash('Invalid username/email or password.', 'danger')
                return render_template('login.html')

            if not user['is_active']:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('login.html')

            # Authenticate session
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']

            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        return render_template('login.html')

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if 'user_id' in session and session.get('user_role') == 'admin':
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Admin username and password required.', 'danger')
                return render_template('admin_login.html')

            user = query_db("""
                SELECT id, name, email, username, password_hash, role, is_active
                FROM users
                WHERE (LOWER(username) = ? OR LOWER(email) = ?)
            """, (username, username), one=True)

            if not user or not check_password_hash(user['password_hash'], password):
                flash('Invalid administrator credentials.', 'danger')
                return render_template('admin_login.html')

            if user['role'] != 'admin':
                flash('Access denied. This account does not possess administrator credentials.', 'danger')
                return render_template('admin_login.html')

            if not user['is_active']:
                flash('Administrator account has been deactivated.', 'danger')
                return render_template('admin_login.html')

            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = 'admin'

            flash('Administrator authenticated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))

        return render_template('admin_login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been safely signed out.', 'info')
        return redirect(url_for('index'))

    # --------------------------------------------------------------------------
    # User Dashboard
    # --------------------------------------------------------------------------
    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = session['user_id']

        # Total user classifications
        total_classifications = query_db(
            "SELECT COUNT(*) FROM predictions WHERE user_id = ?",
            (user_id,), one=True
        )['COUNT(*)']

        # Active & completed pickups for user
        active_pickups_count = query_db("""
            SELECT COUNT(*) FROM pickup_requests
            WHERE user_id = ? AND status IN ('Pending', 'Confirmed', 'Picked Up')
        """, (user_id,), one=True)['COUNT(*)']

        completed_pickups_count = query_db("""
            SELECT COUNT(*) FROM pickup_requests
            WHERE user_id = ? AND status = 'Completed'
        """, (user_id,), one=True)['COUNT(*)']

        # Recent classifications (top 5)
        recent_predictions = query_db("""
            SELECT p.id, p.input_text, p.confidence_score, p.created_at,
                   c.category_name, c.badge_color, c.icon
            FROM predictions p
            JOIN categories c ON p.predicted_category_id = c.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
            LIMIT 5
        """, (user_id,))

        # Active pickup requests (top 5)
        active_pickups = query_db("""
            SELECT r.id, r.address, r.phone, r.preferred_date, r.status, r.created_at,
                   p.name as provider_name, c.category_name, c.badge_color
            FROM pickup_requests r
            JOIN service_providers p ON r.provider_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE r.user_id = ? AND r.status IN ('Pending', 'Confirmed', 'Picked Up')
            ORDER BY r.created_at DESC
            LIMIT 5
        """, (user_id,))

        return render_template(
            'dashboard.html',
            total_classifications=total_classifications,
            active_pickups_count=active_pickups_count,
            completed_pickups_count=completed_pickups_count,
            recent_predictions=recent_predictions,
            active_pickups=active_pickups
        )

    # --------------------------------------------------------------------------
    # AI Classification Module
    # --------------------------------------------------------------------------
    @app.route('/classify')
    def classify():
        return render_template('classify.html')

    @app.route('/classify/predict', methods=['POST'])
    @login_required
    def predict_classification():
        description = request.form.get('description', '').strip()
        if not description:
            flash('Please enter a description of the electronic item.', 'danger')
            return redirect(url_for('classify'))

        classifier = get_classifier()
        try:
            result = classifier.classify(description)
        except Exception as e:
            flash(f'Classification error: {str(e)}', 'danger')
            return redirect(url_for('classify'))

        user_id = session['user_id']
        category_id = result['category_id']
        confidence = result['confidence']
        model_used = result['model_used']
        nlp_pred = result['nlp_details']['predicted_category']
        dl_pred = result['dl_details']['predicted_category']

        # Save to database
        sql = """
            INSERT INTO predictions (
                user_id, input_text, predicted_category_id, confidence_score, model_used, nlp_prediction, dl_prediction
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        pred_id, _ = execute_db(sql, (
            user_id, description, category_id, confidence, model_used, nlp_pred, dl_pred
        ))

        return redirect(url_for('view_result', prediction_id=pred_id))

    @app.route('/result/<int:prediction_id>')
    @login_required
    def view_result(prediction_id):
        user_id = session['user_id']
        pred = query_db("""
            SELECT p.id, p.user_id, p.input_text, p.predicted_category_id, p.confidence_score,
                   p.model_used, p.nlp_prediction, p.dl_prediction, p.created_at,
                   c.category_name, c.description as category_description, c.badge_color, c.icon
            FROM predictions p
            JOIN categories c ON p.predicted_category_id = c.id
            WHERE p.id = ?
        """, (prediction_id,), one=True)

        if not pred:
            abort(404)

        # User isolation: only owner or admin can view
        if pred['user_id'] != user_id and session.get('user_role') != 'admin':
            flash('You do not have permission to view that prediction record.', 'danger')
            return redirect(url_for('dashboard'))

        recommendation = get_recommendation_by_category(pred['predicted_category_id'])

        return render_template('result.html', prediction=pred, recommendation=recommendation)

    # --------------------------------------------------------------------------
    # Prediction History Module
    # --------------------------------------------------------------------------
    @app.route('/history')
    @login_required
    def history():
        user_id = session['user_id']
        history_items = query_db("""
            SELECT p.id, p.input_text, p.predicted_category_id, p.confidence_score, p.created_at,
                   c.category_name, c.badge_color, c.icon
            FROM predictions p
            JOIN categories c ON p.predicted_category_id = c.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        """, (user_id,))
        return render_template('history.html', history=history_items)

    # --------------------------------------------------------------------------
    # Nearby Service Providers & Map Module
    # --------------------------------------------------------------------------
    @app.route('/providers')
    def providers():
        # Read parameters
        lat_arg = request.args.get('lat')
        lon_arg = request.args.get('lon')
        city_arg = request.args.get('city')
        category_id_arg = request.args.get('category_id')
        radius_arg = request.args.get('radius', 25)
        prediction_id_arg = request.args.get('prediction_id')

        try:
            radius_km = float(radius_arg)
        except (ValueError, TypeError):
            radius_km = 25.0

        search_lat = None
        search_lon = None
        selected_city = None

        if lat_arg and lon_arg:
            try:
                search_lat = float(lat_arg)
                search_lon = float(lon_arg)
            except (ValueError, TypeError):
                pass

        if search_lat is None and city_arg:
            city_coords = get_city_coordinates(city_arg)
            if city_coords:
                search_lat = city_coords['lat']
                search_lon = city_coords['lon']
                selected_city = city_arg.lower()

        # Default fallback city is Bengaluru (tech hub) if neither GPS nor city provided
        if search_lat is None:
            default_coords = get_city_coordinates('bengaluru')
            search_lat = default_coords['lat']
            search_lon = default_coords['lon']
            selected_city = 'bengaluru'

        selected_cat_id = int(category_id_arg) if category_id_arg and category_id_arg.isdigit() else None

        result = find_nearby_providers(
            user_lat=search_lat,
            user_lon=search_lon,
            category_id=selected_cat_id,
            radius_km=radius_km,
            limit=5
        )

        categories = query_db("SELECT id, category_name FROM categories ORDER BY id")

        # If linked prediction passed, load it
        linked_prediction = None
        if prediction_id_arg and prediction_id_arg.isdigit():
            linked_prediction = query_db("SELECT id, input_text, predicted_category_id FROM predictions WHERE id = ?", (int(prediction_id_arg),), one=True)

        return render_template(
            'providers.html',
            providers=result['providers'],
            search_lat=search_lat,
            search_lon=search_lon,
            selected_city=selected_city,
            selected_category_id=selected_cat_id,
            radius_km=radius_km,
            categories=categories,
            prediction_id=prediction_id_arg,
            prediction=linked_prediction
        )

    # --------------------------------------------------------------------------
    # Pickup Request Module
    # --------------------------------------------------------------------------
    @app.route('/pickup/request/<int:provider_id>')
    @login_required
    def request_pickup(provider_id):
        provider = query_db("""
            SELECT p.id, p.name, p.category_id, p.phone, p.email, p.address, p.city, p.offers_pickup,
                   c.category_name, c.badge_color, c.icon
            FROM service_providers p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (provider_id,), one=True)

        if not provider:
            flash('Selected service provider was not found.', 'danger')
            return redirect(url_for('providers'))

        if not provider['offers_pickup']:
            flash('This provider does not offer doorstep collection. Please visit their facility for in-person drop-off.', 'warning')
            return redirect(url_for('providers'))

        prediction_id = request.args.get('prediction_id')
        prediction = None
        if prediction_id and prediction_id.isdigit():
            prediction = query_db(
                "SELECT id, input_text, predicted_category_id FROM predictions WHERE id = ? AND user_id = ?",
                (int(prediction_id), session['user_id']), one=True
            )

        min_date = date.today().strftime('%Y-%m-%d')
        return render_template('pickup_request.html', provider=provider, prediction=prediction, min_date=min_date)

    @app.route('/pickup/submit', methods=['POST'])
    @login_required
    def submit_pickup_request():
        user_id = session['user_id']
        provider_id = request.form.get('provider_id')
        prediction_id = request.form.get('prediction_id')
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        preferred_date = request.form.get('preferred_date', '').strip()
        instructions = request.form.get('instructions', '').strip()

        try:
            p_id = int(provider_id)
            pred_id = int(prediction_id) if prediction_id and prediction_id.isdigit() else None
            req_id = create_pickup_request(
                user_id=user_id,
                provider_id=p_id,
                address=address,
                phone=phone,
                preferred_date=preferred_date,
                prediction_id=pred_id,
                instructions=instructions
            )
            flash('Doorstep pickup request scheduled successfully! Tracking reference created.', 'success')
            return redirect(url_for('my_pickups'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('request_pickup', provider_id=provider_id, prediction_id=prediction_id))

    @app.route('/my-pickups')
    @login_required
    def my_pickups():
        user_id = session['user_id']
        pickups = get_user_pickups(user_id)
        return render_template('my_pickups.html', pickups=pickups)

    @app.route('/pickup/cancel/<int:request_id>', methods=['POST'])
    @login_required
    def cancel_pickup(request_id):
        user_id = session['user_id']
        try:
            cancel_user_pickup(request_id, user_id)
            flash('Your pickup request has been cancelled.', 'info')
        except (ValueError, PermissionError) as e:
            flash(str(e), 'danger')
        return redirect(url_for('my_pickups'))

    # --------------------------------------------------------------------------
    # Admin Panel Routes (Protected by @admin_required)
    # --------------------------------------------------------------------------
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        stats = {
            'total_users': query_db("SELECT COUNT(*) FROM users", one=True)['COUNT(*)'],
            'total_predictions': query_db("SELECT COUNT(*) FROM predictions", one=True)['COUNT(*)'],
            'total_providers': query_db("SELECT COUNT(*) FROM service_providers", one=True)['COUNT(*)'],
            'pending_pickups': query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Pending'", one=True)['COUNT(*)'],
            'completed_pickups': query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Completed'", one=True)['COUNT(*)']
        }
        recent_predictions = query_db("""
            SELECT p.id, p.input_text, p.confidence_score, p.model_used, p.created_at,
                   u.name as user_name, c.category_name, c.badge_color
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            JOIN categories c ON p.predicted_category_id = c.id
            ORDER BY p.created_at DESC
            LIMIT 6
        """)
        return render_template('admin_dashboard.html', stats=stats, recent_predictions=recent_predictions)

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        users = query_db("SELECT id, name, email, username, role, is_active, created_at FROM users ORDER BY created_at DESC")
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_toggle_user_status(user_id):
        if user_id == session.get('user_id'):
            flash('Cannot deactivate the current active administrator session.', 'warning')
            return redirect(url_for('admin_users'))

        user = query_db("SELECT is_active, username FROM users WHERE id = ?", (user_id,), one=True)
        if user:
            new_status = 0 if user['is_active'] else 1
            execute_db("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
            action = "activated" if new_status else "deactivated"
            flash(f"User account '{user['username']}' has been {action}.", 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_delete_user(user_id):
        if user_id == session.get('user_id'):
            flash('Cannot delete your own administrator account.', 'danger')
            return redirect(url_for('admin_users'))

        execute_db("DELETE FROM users WHERE id = ?", (user_id,))
        flash('User account deleted permanently.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/predictions')
    @admin_required
    def admin_predictions():
        q = request.args.get('q', '').strip()
        cat_id = request.args.get('category_id')

        sql = """
            SELECT p.id, p.input_text, p.confidence_score, p.model_used, p.nlp_prediction, p.dl_prediction, p.created_at,
                   u.name as user_name, u.email as user_email,
                   c.category_name, c.badge_color
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            JOIN categories c ON p.predicted_category_id = c.id
            WHERE 1=1
        """
        params = []
        if q:
            sql += " AND p.input_text LIKE ?"
            params.append(f"%{q}%")
        if cat_id and cat_id.isdigit():
            sql += " AND p.predicted_category_id = ?"
            params.append(int(cat_id))

        sql += " ORDER BY p.created_at DESC"
        predictions = query_db(sql, tuple(params))
        categories = query_db("SELECT id, category_name FROM categories ORDER BY id")
        selected_cat = int(cat_id) if cat_id and cat_id.isdigit() else None

        return render_template(
            'admin_predictions.html',
            predictions=predictions,
            categories=categories,
            search_query=q,
            selected_category_id=selected_cat
        )

    @app.route('/admin/predictions/delete/<int:prediction_id>', methods=['POST'])
    @admin_required
    def admin_delete_prediction(prediction_id):
        execute_db("DELETE FROM predictions WHERE id = ?", (prediction_id,))
        flash('Prediction log record deleted.', 'info')
        return redirect(url_for('admin_predictions'))

    @app.route('/admin/categories')
    @admin_required
    def admin_categories():
        categories = query_db("SELECT id FROM categories ORDER BY id")
        categories_data = [get_recommendation_by_category(c['id']) for c in categories]
        return render_template('admin_categories.html', categories_data=categories_data)

    @app.route('/admin/categories/update/<int:category_id>', methods=['POST'])
    @admin_required
    def admin_update_category(category_id):
        cat_desc = request.form.get('cat_description', '').strip()
        rec_text = request.form.get('recommendation_text', '').strip()
        instructions = request.form.get('instructions', '').strip()
        safety = request.form.get('safety_guidelines', '').strip()

        if cat_desc:
            execute_db("UPDATE categories SET description = ? WHERE id = ?", (cat_desc, category_id))

        update_recommendation(category_id, rec_text, instructions, safety)
        flash('Category details and recommendation directives updated successfully.', 'success')
        return redirect(url_for('admin_categories'))

    @app.route('/admin/providers')
    @admin_required
    def admin_providers():
        providers = query_db("""
            SELECT p.id, p.name, p.category_id, p.phone, p.email, p.address, p.city,
                   p.latitude, p.longitude, p.offers_pickup, p.is_active, p.verification_status,
                   c.category_name, c.badge_color
            FROM service_providers p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id DESC
        """)
        categories = query_db("SELECT id, category_name FROM categories ORDER BY id")
        return render_template('admin_providers.html', providers=providers, categories=categories)

    @app.route('/admin/providers/add', methods=['POST'])
    @admin_required
    def admin_add_provider():
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        offers_pickup = 1 if request.form.get('offers_pickup') else 0
        verification_status = request.form.get('verification_status', 'Demo / Sample')

        try:
            lat = float(latitude)
            lon = float(longitude)
            cat_id = int(category_id)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Latitude must be between -90 and 90, longitude between -180 and 180.")
            if not name or not phone or not address or not city:
                raise ValueError("All mandatory provider fields must be filled.")

            execute_db("""
                INSERT INTO service_providers (
                    name, category_id, phone, email, address, city, latitude, longitude, offers_pickup, is_active, verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (name, cat_id, phone, email, address, city, lat, lon, offers_pickup, verification_status))
            flash(f"Service provider '{name}' added successfully.", 'success')
        except ValueError as e:
            flash(f"Error adding provider: {str(e)}", 'danger')

        return redirect(url_for('admin_providers'))

    @app.route('/admin/providers/toggle/<int:provider_id>', methods=['POST'])
    @admin_required
    def admin_toggle_provider_status(provider_id):
        p = query_db("SELECT is_active, name FROM service_providers WHERE id = ?", (provider_id,), one=True)
        if p:
            new_val = 0 if p['is_active'] else 1
            execute_db("UPDATE service_providers SET is_active = ? WHERE id = ?", (new_val, provider_id))
            flash(f"Provider '{p['name']}' status updated to {'Active' if new_val else 'Inactive'}.", 'info')
        return redirect(url_for('admin_providers'))

    @app.route('/admin/providers/delete/<int:provider_id>', methods=['POST'])
    @admin_required
    def admin_delete_provider(provider_id):
        execute_db("DELETE FROM service_providers WHERE id = ?", (provider_id,))
        flash('Service provider record deleted.', 'info')
        return redirect(url_for('admin_providers'))

    @app.route('/admin/pickups')
    @admin_required
    def admin_pickups():
        status_filter = request.args.get('status')
        pickups = get_all_pickups(status_filter=status_filter)

        all_count = query_db("SELECT COUNT(*) FROM pickup_requests", one=True)['COUNT(*)']
        pending_count = query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Pending'", one=True)['COUNT(*)']
        confirmed_count = query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Confirmed'", one=True)['COUNT(*)']
        picked_up_count = query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Picked Up'", one=True)['COUNT(*)']
        completed_count = query_db("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Completed'", one=True)['COUNT(*)']

        return render_template(
            'admin_pickups.html',
            pickups=pickups,
            status_filter=status_filter,
            all_count=all_count,
            pending_count=pending_count,
            confirmed_count=confirmed_count,
            picked_up_count=picked_up_count,
            completed_count=completed_count
        )

    @app.route('/admin/pickups/update/<int:request_id>', methods=['POST'])
    @admin_required
    def admin_update_pickup_status(request_id):
        new_status = request.form.get('new_status')
        notes = request.form.get('notes', '').strip()
        try:
            update_pickup_status(request_id, new_status, notes=notes)
            flash(f'Pickup request #REQ-{request_id} updated to {new_status}.', 'success')
        except ValueError as e:
            flash(str(e), 'danger')
        return redirect(url_for('admin_pickups'))

    # --------------------------------------------------------------------------
    # Error Handlers
    # --------------------------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', content='<div class="container py-5 text-center"><h1>404</h1><p>Page Not Found.</p><a href="/" class="btn btn-eco-primary">Return Home</a></div>'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', content='<div class="container py-5 text-center"><h1>500</h1><p>An internal error occurred.</p><a href="/" class="btn btn-eco-primary">Return Home</a></div>'), 500

    return app

# Main entry point
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
