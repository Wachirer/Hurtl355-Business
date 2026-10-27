"""
Hurtl355 — local development entry point.
Run with:  python run.py   (or: flask --app wsgi run)

Production uses wsgi.py via gunicorn — see render.yaml.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG") == "1",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
    )
