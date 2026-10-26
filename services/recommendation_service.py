"""
EcoAI Recommendation Service
Retrieves and manages recommendation text, actionable steps, and safety guidelines
from the SQLite database.
"""

from database.db import query_db, execute_db

def get_recommendation_by_category(category_name_or_id, db_path=None):
    """
    Fetch recommendation and category details by category name or category ID.
    Returns structured dict with action items and safety tips.
    """
    if isinstance(category_name_or_id, int) or (isinstance(category_name_or_id, str) and category_name_or_id.isdigit()):
        cat_id = int(category_name_or_id)
        query = """
            SELECT c.id as category_id, c.category_name, c.description, c.badge_color, c.icon,
                   r.id as rec_id, r.recommendation_text, r.instructions, r.safety_guidelines
            FROM categories c
            LEFT JOIN recommendations r ON c.id = r.category_id
            WHERE c.id = ?
        """
        row = query_db(query, (cat_id,), one=True, db_path=db_path)
    else:
        query = """
            SELECT c.id as category_id, c.category_name, c.description, c.badge_color, c.icon,
                   r.id as rec_id, r.recommendation_text, r.instructions, r.safety_guidelines
            FROM categories c
            LEFT JOIN recommendations r ON c.id = r.category_id
            WHERE LOWER(c.category_name) = LOWER(?)
        """
        row = query_db(query, (category_name_or_id,), one=True, db_path=db_path)

    if not row:
        return None

    # Parse instructions into list of step strings
    instructions_raw = row['instructions'] or ""
    step_list = [line.strip() for line in instructions_raw.split('\n') if line.strip()]

    return {
        'category_id': row['category_id'],
        'category_name': row['category_name'],
        'description': row['description'],
        'badge_color': row['badge_color'] or 'success',
        'icon': row['icon'] or 'bi-cpu',
        'recommendation_text': row['recommendation_text'] or 'No recommendation available yet.',
        'instructions_raw': instructions_raw,
        'steps': step_list,
        'safety_guidelines': row['safety_guidelines'] or 'Practice general electronic safety.'
    }

def update_recommendation(category_id, recommendation_text=None, instructions=None, safety_guidelines=None, db_path=None, **kwargs):
    """Update or insert recommendation content in the database."""
    # Support positional or keyword arguments
    rec_text = recommendation_text or kwargs.get('rec_text', '')
    inst = instructions or kwargs.get('instructions', '')
    safe = safety_guidelines or kwargs.get('safety_guidelines', '')

    existing = query_db("SELECT id FROM recommendations WHERE category_id = ?", (category_id,), one=True, db_path=db_path)
    if existing:
        query = """
            UPDATE recommendations
            SET recommendation_text = ?, instructions = ?, safety_guidelines = ?
            WHERE category_id = ?
        """
        execute_db(query, (rec_text, inst, safe, category_id), db_path=db_path)
    else:
        query = """
            INSERT INTO recommendations (category_id, recommendation_text, instructions, safety_guidelines)
            VALUES (?, ?, ?, ?)
        """
        execute_db(query, (category_id, rec_text, inst, safe), db_path=db_path)
    return True
