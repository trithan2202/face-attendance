from datetime import time

from backend.app.core.database import get_db_session
from backend.app.repositories.shift_repository import ShiftRepository


def main():
    db = get_db_session()

    try:
        shift = ShiftRepository.get_by_code(
            db,
            "HC"
        )

        if shift:
            print("[INFO] Shift HC already exists")
            return

        ShiftRepository.create(
            db,
            code="HC",
            name="Hanh chinh",
            start_time=time(8, 0),
            end_time=time(17, 0),
            late_grace_minutes=10,
            early_leave_grace_minutes=10,
            cross_day=False
        )

        db.commit()

        print("[OK] Shift HC created")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()