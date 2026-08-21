from backend.app.core.database import get_db_session
from backend.app.repositories.department_repository import DepartmentRepository


DEFAULT_DEPARTMENTS = (
    ("KT", "Ky thuat"),
    ("NS", "Nhan su"),
    ("KD", "Kinh doanh"),
)


def main():
    db = get_db_session()

    try:
        created = 0

        for code, name in DEFAULT_DEPARTMENTS:
            if DepartmentRepository.get_by_code(db, code):
                continue

            DepartmentRepository.create(
                db,
                code=code,
                name=name
            )
            created += 1

        if not created:
            print("[INFO] Default departments already exist")
            return

        db.commit()

        print(f"[OK] {created} department(s) created")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
