"""
EcoAI WSGI Production Entry Point
Compatible with Gunicorn, Waitress, uWSGI, and cloud serverless platforms.
"""

from app import create_app

app = create_app('production')

if __name__ == "__main__":
    app.run()
