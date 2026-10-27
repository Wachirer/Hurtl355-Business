"""
Create the admin user, or change its password, in whatever database
DATABASE_URL points to. Run from your computer:

    $env:DATABASE_URL = "postgresql://...neon.tech/neondb?sslmode=require"
    python scripts/set_admin_password.py
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app, db  # noqa: E402
from app.models.user import User  # noqa: E402


def main() -> None:
    username = input("Admin username [admin]: ").strip() or "admin"
    password = getpass.getpass("New password (min 12 characters): ")
    if len(password) < 12:
        sys.exit("Password too short.")
    if password != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match.")

    with create_app().app_context():
        user = User.query.filter_by(username=username).first()
        if user is None:
            email = input("Email: ").strip() or "admin@hurtl355.com"
            user = User(username=username, email=email)
            db.session.add(user)
        user.set_password(password)
        db.session.commit()
        print(f"Password set for '{username}'.")


if __name__ == "__main__":
    main()
