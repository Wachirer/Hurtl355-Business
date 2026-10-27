"""
Copy all data from your local SQLite file into the database in DATABASE_URL
(Neon). Run it ONCE from your own computer.

    # PowerShell
    $env:DATABASE_URL = "postgresql://...neon.tech/neondb?sslmode=require"
    python scripts/migrate_sqlite_to_postgres.py instance/hurtl355.db

Refuses to run if the target already has data (add --force to override).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text  # noqa: E402

from app import create_app, db  # noqa: E402
import app.models  # noqa: E402,F401  (registers all tables)

ORDER = ["users", "site_settings", "works", "pricing_packages",
         "pricing_features", "testimonials", "messages"]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    if not args or not os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql://")):
        sys.exit("Usage: set DATABASE_URL to your Postgres URL, then:\n"
                 "  python scripts/migrate_sqlite_to_postgres.py path/to/hurtl355.db")

    source = create_engine(f"sqlite:///{os.path.abspath(args[0])}")
    flask_app = create_app()

    with flask_app.app_context():
        target = db.engine
        tables = {t: db.metadata.tables[t] for t in ORDER}

        with target.connect() as tc:
            existing = {t: tc.execute(tables[t].select().limit(1)).first() is not None for t in ORDER}
        if any(existing.values()) and not force:
            sys.exit("Target database already contains data. Re-run with --force to add anyway "
                     "(may fail on duplicate ids), or empty the tables first.")

        with source.connect() as sc, target.begin() as tc:
            for name in ORDER:
                rows = [dict(r._mapping) for r in sc.execute(tables[name].select())]
                if rows:
                    tc.execute(tables[name].insert(), rows)
                print(f"  {name}: {len(rows)} rows")
            if target.dialect.name == "postgresql":
                for name in ORDER:
                    tc.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {name}), 1))"
                    ))
        print("Done. Next: python scripts/set_admin_password.py")


if __name__ == "__main__":
    main()
