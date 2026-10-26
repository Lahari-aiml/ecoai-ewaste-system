"""
EcoAI Vercel Serverless Entrypoint
Exposes the Flask WSGI application for Vercel Python runtime.
Handles read-only serverless filesystem by copying pre-seeded SQLite DB to /tmp.
"""

import sys
import os
import shutil
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup writable database for Vercel Serverless Environment
if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    tmp_dir = Path('/tmp')
    tmp_db = tmp_dir / 'ecoai.db'
    src_db = BASE_DIR / 'database' / 'ecoai.db'

    if not tmp_db.exists():
        if src_db.exists():
            shutil.copy(src_db, tmp_db)
        else:
            from database.seed import seed_database
            seed_database(str(tmp_db))

    os.environ['ECOAI_DATABASE'] = str(tmp_db)

from app import app

# Vercel searches for 'app' or 'handler'
handler = app

if __name__ == "__main__":
    app.run()
