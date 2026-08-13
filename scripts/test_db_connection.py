from sqlalchemy import text

from backend.app.core.database import get_db_session


def main():
    db = get_db_session()

    try:
        result = db.execute(
            text("SELECT version()")
        )

        version = result.scalar()

        print("[OK] PostgreSQL connected")
        print(version)

    finally:
        db.close()


if __name__ == "__main__":
    main()