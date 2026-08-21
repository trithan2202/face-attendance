from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.repositories.system_setting_repository import (
    SystemSettingRepository,
)
from backend.app.services.settings_service import EDITABLE_SETTINGS


def main():
    db = get_db_session()

    try:
        created = 0

        for key, definition in EDITABLE_SETTINGS.items():
            if SystemSettingRepository.get_by_key(db, key):
                continue

            SystemSettingRepository.upsert(
                db,
                key=key,
                value=str(getattr(settings, key)),
                value_type=definition.value_type,
                description=definition.description,
            )
            created += 1

        if not created:
            print("[INFO] System settings already exist")
            return

        db.commit()

        print(f"[OK] {created} system setting(s) created")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
