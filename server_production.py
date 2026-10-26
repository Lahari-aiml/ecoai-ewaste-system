"""
EcoAI Production Server Launcher
Uses Waitress (production-grade pure-Python WSGI server)
Suitable for Windows, Linux, and macOS production deployments.
"""

import os
import sys
from waitress import serve
from wsgi import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    threads = int(os.environ.get('THREADS', 4))

    print("=" * 65)
    print("  EcoAI – Intelligent E-Waste Management System (Production WSGI)")
    print("=" * 65)
    print(f"[*] Serving on http://{host}:{port} with {threads} worker threads...")
    print(f"[*] Local access: http://127.0.0.1:{port}")
    print("[*] Press Ctrl+C to terminate the production server.")
    print("=" * 65)

    serve(app, host=host, port=port, threads=threads)
