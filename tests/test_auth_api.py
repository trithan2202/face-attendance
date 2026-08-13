import unittest
import time

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.models  # noqa: F401
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.models import AdminUser
from backend.app.services.liveness import liveness_service


class AuthApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_secret = settings.JWT_SECRET
        settings.JWT_SECRET = "integration-test-secret-at-least-32-bytes"
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        with cls.Session() as db:
            db.add(
                AdminUser(
                    username="admin",
                    password_hash=hash_password("correct-password"),
                    is_active=True,
                )
            )
            db.commit()

        def override_db():
            with cls.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()
        settings.JWT_SECRET = cls.original_secret

    def setUp(self):
        self.client.cookies.clear()

    def login(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "correct-password"},
        )
        self.assertEqual(response.status_code, 200)

    def test_login_me_and_logout(self):
        failed = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        self.assertEqual(failed.status_code, 401)
        self.assertEqual(failed.json()["code"], "UNAUTHORIZED")

        logged_in = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "correct-password"},
        )
        self.assertEqual(logged_in.status_code, 200)
        self.assertIn("access_token", self.client.cookies)

        current = self.client.get("/api/auth/me")
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["username"], "admin")

        logged_out = self.client.post("/api/auth/logout")
        self.assertEqual(logged_out.status_code, 204)
        self.assertNotIn("access_token", self.client.cookies)

    def test_public_liveness_session_can_start_and_cancel(self):
        started = self.client.post("/api/kiosk/liveness")
        self.assertEqual(started.status_code, 201)
        self.assertIn(started.json()["challenge"], {"BLINK", "TURN_LEFT", "TURN_RIGHT"})
        session_id = started.json()["session_id"]
        status_response = self.client.get(f"/api/kiosk/liveness/{session_id}")
        self.assertEqual(status_response.status_code, 200)
        cancelled = self.client.delete(f"/api/kiosk/liveness/{session_id}")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["state"], "CANCELLED")

    def test_liveness_proof_is_single_use_for_recognition(self):
        proof = liveness_service.start()
        proof.state = "PASSED"
        proof.passed_at = time.monotonic()
        first = self.client.post(
            "/api/kiosk/recognition",
            json={"liveness_session_id": proof.session_id},
        )
        self.assertEqual(first.status_code, 201)
        reused = self.client.post(
            "/api/kiosk/recognition",
            json={"liveness_session_id": proof.session_id},
        )
        self.assertEqual(reused.status_code, 409)

    def test_admin_shift_and_employee_crud(self):
        unauthorized = self.client.get("/api/admin/shifts")
        self.assertEqual(unauthorized.status_code, 401)
        self.login()

        shift_payload = {
            "code": "HC",
            "name": "Hành chính",
            "start_time": "08:00:00",
            "end_time": "17:00:00",
            "late_grace_minutes": 10,
            "early_leave_grace_minutes": 10,
            "cross_day": False,
        }
        created_shift = self.client.post("/api/admin/shifts", json=shift_payload)
        self.assertEqual(created_shift.status_code, 201)
        shift_id = created_shift.json()["id"]

        duplicate_shift = self.client.post("/api/admin/shifts", json=shift_payload)
        self.assertEqual(duplicate_shift.status_code, 409)

        employee_payload = {
            "employee_code": "NV001",
            "full_name": "Nguyễn Văn A",
            "email": "nva@example.com",
            "phone": "0900000000",
            "department": "Kỹ thuật",
            "shift_id": shift_id,
        }
        created_employee = self.client.post(
            "/api/admin/employees", json=employee_payload
        )
        self.assertEqual(created_employee.status_code, 201)
        employee = created_employee.json()
        self.assertEqual(employee["status"], "PENDING_ENROLLMENT")
        self.assertEqual(employee["enrollment_status"], "NOT_STARTED")

        started = self.client.post(
            f"/api/admin/employees/{employee['id']}/enrollment"
        )
        self.assertEqual(started.status_code, 201)
        session_id = started.json()["session_id"]
        session_status = self.client.get(
            f"/api/admin/enrollment/{session_id}"
        )
        self.assertEqual(session_status.status_code, 200)
        self.assertEqual(session_status.json()["state"], "CAPTURING")
        invalid_frame = self.client.post(
            f"/api/admin/enrollment/{session_id}/frame",
            files={"frame": ("frame.txt", b"invalid", "text/plain")},
        )
        self.assertEqual(invalid_frame.status_code, 415)
        cancelled = self.client.delete(
            f"/api/admin/enrollment/{session_id}"
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["state"], "CANCELLED")

        activate_payload = {**employee_payload, "status": "ACTIVE"}
        activate = self.client.put(
            f"/api/admin/employees/{employee['id']}", json=activate_payload
        )
        self.assertEqual(activate.status_code, 409)

        delete_used_shift = self.client.delete(f"/api/admin/shifts/{shift_id}")
        self.assertEqual(delete_used_shift.status_code, 409)

        deactivate = self.client.delete(
            f"/api/admin/employees/{employee['id']}"
        )
        self.assertEqual(deactivate.status_code, 204)
        filtered = self.client.get("/api/admin/employees?status=INACTIVE")
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(len(filtered.json()), 1)


if __name__ == "__main__":
    unittest.main()
