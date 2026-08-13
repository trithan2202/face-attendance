from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from backend.app.core.database import engine


LEGACY_TABLES = {
    "attendance_daily",
    "attendance_events",
    "employees",
    "face_embeddings",
    "shifts",
}


def main():
    tables = set(inspect(engine).get_table_names())
    config = Config("alembic.ini")

    if "alembic_version" not in tables:
        if not tables:
            print("[DB] Empty database; applying all migrations")
        elif LEGACY_TABLES.issubset(tables):
            print("[DB] Legacy schema detected; adopting it at revision 0001")
            command.stamp(config, "20260813_0001")
        else:
            unexpected = ", ".join(sorted(tables))
            raise RuntimeError(
                "Database has an unknown partial schema and cannot be adopted "
                f"automatically. Existing tables: {unexpected}"
            )

    command.upgrade(config, "head")

    from scripts.seed_shift import main as seed_shift
    from scripts.seed_admin import main as seed_admin

    seed_shift()
    seed_admin()
    print("[DB] Migrations and seed completed")


if __name__ == "__main__":
    main()
