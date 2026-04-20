"""Hard reset PostgreSQL schema and re-apply Alembic migrations.

WARNING: This permanently deletes all data in the target schema.
"""

from __future__ import annotations

import subprocess

from sqlalchemy import create_engine, text

from app.core.config import settings


def reset_schema() -> None:
    """Drop and recreate the public schema, including alembic_version."""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()


def run_migrations() -> None:
    """Run Alembic upgrades from base to head."""
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def main() -> int:
    try:
        print("Resetting PostgreSQL schema 'public'...")
        reset_schema()
        print("Applying Alembic migrations...")
        run_migrations()
    except subprocess.CalledProcessError as exc:
        print(f"Migration command failed with exit code {exc.returncode}")
        return exc.returncode
    except Exception as exc:  # pragma: no cover
        print(f"Reset failed: {exc}")
        return 1

    print("Database reset complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
