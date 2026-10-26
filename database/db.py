import sqlite3
import os
from flask import g, current_app
from config import BASE_DIR, Config

def get_db_path():
    """Get configured database path."""
    if current_app:
        return current_app.config.get('DATABASE', Config.DATABASE)
    return Config.DATABASE

def get_db(db_path=None):
    """
    Open a new database connection if there is none yet for the
    current application context.
    """
    target_path = db_path or get_db_path()

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    if current_app:
        if 'db' not in g or g.get('db_path') != target_path:
            g.db = sqlite3.connect(target_path, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
            g.db_path = target_path
        return g.db
    else:
        conn = sqlite3.connect(target_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def close_db(e=None):
    """Close the database connection on request teardown."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """Initialize database using schema.sql."""
    target_path = db_path or get_db_path()
    schema_file = BASE_DIR / 'database' / 'schema.sql'

    conn = get_db(target_path)
    with open(schema_file, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    if not current_app:
        conn.close()

def query_db(query, args=(), one=False, db_path=None):
    """Convenience helper to query the database and fetch rows as dicts."""
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if not current_app and db_path:
        conn.close()
    if rv:
        return (dict(rv[0])) if one else [dict(row) for row in rv]
    return None if one else []

def execute_db(query, args=(), db_path=None):
    """Convenience helper to execute insert/update/delete and return lastrowid."""
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    row_count = cur.rowcount
    cur.close()
    if not current_app and db_path:
        conn.close()
    return last_id, row_count
