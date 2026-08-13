import unittest
from datetime import date, datetime, time

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.models  # noqa: F401
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.models import (
    AdminUser,
    AttendanceAdjustment,
    AttendanceDaily,
    AttendanceEvent,
    Employee,
    Shift,
)


class AttendanceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_secret = settings.JWT_SECRET
        settings.JWT_SECRET = "attendance-test-secret-at-least-32-bytes"
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        with cls.Session() as db:
            admin = AdminUser(
                username="attendance-admin",
                password_hash=hash_password("correct-password"),
                is_active=True,
            )
            shift = Shift(
                code="HC-ATT",
                name="Hành chính",
                start_time=time(8),
                end_time=time(17),
                late_grace_minutes=10,
                early_leave_grace_minutes=10,
                cross_day=False,
            )
            db.add_all([admin, shift])
            db.flush()
            employee = Employee(
                employee_code="NV-ATT",
                full_name="Attendance Test",
                department="QA",
                shift_id=shift.id,
                status="ACTIVE",
            )
            db.add(employee)
            db.flush()
            daily = AttendanceDaily(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date(2026, 8, 13),
                first_check_in=datetime(2026, 8, 13, 8, 5),
                last_check_out=None,
                status="MISSING_CHECK_OUT",
            )
            db.add(daily)
            db.flush()
            db.add(
                AttendanceEvent(
                    employee_id=employee.id,
                    event_type="CHECK_IN",
                    recognized_at=datetime(2026, 8, 13, 8, 5),
                    similarity=0.9,
                    detection_score=0.99,
                )
            )
            db.commit()
            cls.daily_id = daily.id

        def override_db():
            with cls.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)
        login = cls.client.post(
            "/api/auth/login",
            json={
                "username": "attendance-admin",
                "password": "correct-password",
            },
        )
        assert login.status_code == 200

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()
        settings.JWT_SECRET = cls.original_secret

    def test_01_list_detail_adjust_and_audit(self):
        listed = self.client.get(
            "/api/admin/attendance?date_from=2026-08-13&date_to=2026-08-13&department=QA"
        )
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)

        exported = self.client.get(
            "/api/admin/attendance/export.csv?date_from=2026-08-13&date_to=2026-08-13"
        )
        self.assertEqual(exported.status_code, 200)
        self.assertIn("text/csv", exported.headers["content-type"])
        self.assertIn("NV-ATT", exported.content.decode("utf-8-sig"))

        detail = self.client.get(f"/api/admin/attendance/{self.daily_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()["events"]), 1)

        no_change = self.client.patch(
            f"/api/admin/attendance/{self.daily_id}",
            json={"reason": "Không có thay đổi"},
        )
        self.assertEqual(no_change.status_code, 422)

        adjusted = self.client.patch(
            f"/api/admin/attendance/{self.daily_id}",
            json={
                "last_check_out": "2026-08-13T18:00:00",
                "reason": "Bổ sung giờ checkout theo xác nhận quản lý",
            },
        )
        self.assertEqual(adjusted.status_code, 200)
        result = adjusted.json()
        self.assertEqual(result["status"], "PRESENT")
        self.assertEqual(result["worked_minutes"], 595)
        self.assertEqual(result["overtime_minutes"], 60)

        audit = self.client.get(
            f"/api/admin/attendance/{self.daily_id}/adjustments"
        )
        self.assertEqual(audit.status_code, 200)
        self.assertEqual(len(audit.json()), 1)
        self.assertEqual(audit.json()[0]["admin_username"], "attendance-admin")
        self.assertIsNone(audit.json()[0]["before_data"]["last_check_out"])
        self.assertEqual(
            audit.json()[0]["after_data"]["last_check_out"],
            "2026-08-13T18:00:00",
        )

    def test_02_invalid_time_rolls_back_without_audit(self):
        invalid = self.client.patch(
            f"/api/admin/attendance/{self.daily_id}",
            json={
                "last_check_out": "2026-08-13T07:00:00",
                "reason": "Dữ liệu sai để kiểm thử rollback",
            },
        )
        self.assertEqual(invalid.status_code, 422)
        with self.Session() as db:
            count = db.scalar(select(func.count(AttendanceAdjustment.id)))
            self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
