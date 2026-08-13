from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.core.security import hash_password
from backend.app.repositories.admin_user_repository import AdminUserRepository


def main():
    db = get_db_session()
    try:
        existing = AdminUserRepository.get_by_username(db, settings.ADMIN_USERNAME)
        if existing:
            print(f"[INFO] Admin '{settings.ADMIN_USERNAME}' already exists")
            return
        if settings.ADMIN_PASSWORD in {"admin123", "change-me"}:
            raise RuntimeError(
                "Unsafe ADMIN_PASSWORD. Set a non-default password in .env, "
                "then run docker compose up -d again."
            )
        AdminUserRepository.create(
            db,
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
        )
        db.commit()
        print(f"[OK] Admin '{settings.ADMIN_USERNAME}' created")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
