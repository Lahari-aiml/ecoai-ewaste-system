"""
EcoAI Pickup Request Service
Handles doorstep e-waste pickup workflows, status transitions, and user request tracking.
"""

from datetime import datetime, date
import re
from database.db import query_db, execute_db

# Allowed status transitions
VALID_TRANSITIONS = {
    'Pending': ['Confirmed', 'Rejected', 'Cancelled'],
    'Confirmed': ['Picked Up', 'Cancelled'],
    'Picked Up': ['Completed'],
    'Completed': [],
    'Cancelled': [],
    'Rejected': []
}

def validate_pickup_date(date_str: str) -> bool:
    """Validate that date is valid format and not in the past."""
    try:
        p_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return p_date >= date.today()
    except (ValueError, TypeError):
        return False

def validate_phone(phone_str: str) -> bool:
    """Validate phone number has at least 10 digits."""
    if not phone_str:
        return False
    digits = re.sub(r'\D', '', phone_str)
    return len(digits) >= 10

def create_pickup_request(user_id: int, provider_id: int, address: str, phone: str,
                          preferred_date: str, prediction_id=None, instructions="", db_path=None):
    """
    Validate and insert a new pickup request with initial status 'Pending'.
    """
    if not address or not address.strip():
        raise ValueError("Pickup address is required.")

    if not validate_phone(phone):
        raise ValueError("A valid contact phone number with at least 10 digits is required.")

    if not validate_pickup_date(preferred_date):
        raise ValueError("Preferred pickup date must be today or a future date.")

    # Validate provider
    provider = query_db("SELECT id, name, offers_pickup, is_active FROM service_providers WHERE id = ?", (provider_id,), one=True, db_path=db_path)
    if not provider:
        raise ValueError("Selected service provider does not exist.")
    if not provider['is_active']:
        raise ValueError("Selected service provider is currently inactive.")
    if not provider['offers_pickup']:
        raise ValueError("Selected service provider does not offer doorstep pickup service.")

    # Validate prediction if passed
    if prediction_id:
        pred = query_db("SELECT id FROM predictions WHERE id = ? AND user_id = ?", (prediction_id, user_id), one=True, db_path=db_path)
        if not pred:
            prediction_id = None

    sql = """
        INSERT INTO pickup_requests (
            user_id, prediction_id, provider_id, address, phone, preferred_date, instructions, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """
    req_id, _ = execute_db(sql, (
        user_id,
        prediction_id,
        provider_id,
        address.strip(),
        phone.strip(),
        preferred_date.strip(),
        instructions.strip() if instructions else ""
    ), db_path=db_path)
    return req_id

def cancel_user_pickup(request_id: int, user_id: int, db_path=None):
    """
    Allow user to cancel their own request if status is 'Pending'.
    """
    req = query_db("SELECT id, user_id, status FROM pickup_requests WHERE id = ?", (request_id,), one=True, db_path=db_path)
    if not req:
        raise ValueError("Pickup request not found.")

    if req['user_id'] != user_id:
        raise PermissionError("You are not authorized to cancel this request.")

    if req['status'] != 'Pending':
        raise ValueError(f"Cannot cancel request in '{req['status']}' state. Only 'Pending' requests can be cancelled.")

    execute_db("UPDATE pickup_requests SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (request_id,), db_path=db_path)
    return True

def update_pickup_status(request_id: int, new_status: str, notes=None, db_path=None):
    """
    Admin status update with strict transition validation.
    """
    req = query_db("SELECT id, status FROM pickup_requests WHERE id = ?", (request_id,), one=True, db_path=db_path)
    if not req:
        raise ValueError("Pickup request not found.")

    current_status = req['status']
    allowed_next = VALID_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        raise ValueError(f"Invalid status change: Cannot transition from '{current_status}' to '{new_status}'. Allowed next states: {allowed_next or 'None (Terminal state)'}")

    execute_db("""
        UPDATE pickup_requests
        SET status = ?, status_notes = COALESCE(?, status_notes), notes = COALESCE(?, notes), updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, notes, notes, request_id), db_path=db_path)
    return True

def get_user_pickups(user_id: int, db_path=None):
    """Fetch all pickup requests belonging to a specific authenticated user."""
    sql = """
        SELECT r.id, r.address, r.phone, r.preferred_date, r.instructions, r.status, r.status_notes, r.notes,
               r.created_at, r.updated_at,
               p.name as provider_name, p.phone as provider_phone, p.address as provider_address, p.city as provider_city,
               c.category_name, c.badge_color, c.icon,
               pr.input_text as item_description
        FROM pickup_requests r
        JOIN service_providers p ON r.provider_id = p.id
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN predictions pr ON r.prediction_id = pr.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    """
    return query_db(sql, (user_id,), db_path=db_path)

def get_all_pickups(status_filter=None, db_path=None):
    """Fetch all pickup requests for admin overview with optional status filtering."""
    sql = """
        SELECT r.id, r.address, r.phone, r.preferred_date, r.instructions, r.status, r.status_notes, r.notes,
               r.created_at, r.updated_at,
               u.id as user_id, u.name as user_name, u.email as user_email,
               p.name as provider_name, p.city as provider_city,
               c.category_name, c.badge_color,
               pr.input_text as item_description
        FROM pickup_requests r
        JOIN users u ON r.user_id = u.id
        JOIN service_providers p ON r.provider_id = p.id
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN predictions pr ON r.prediction_id = pr.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND r.status = ?"
        params.append(status_filter)
    sql += " ORDER BY r.created_at DESC"
    return query_db(sql, tuple(params), db_path=db_path)
