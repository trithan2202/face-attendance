import unittest
from datetime import time
from types import SimpleNamespace

import numpy as np
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401
from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.models import Employee, FaceEmbedding, Shift
from backend.app.services.enrollment import EnrollmentService, EnrollmentSessionStore


class FakeEngine:
    def detect(self, frame):
        return [
            SimpleNamespace(
                bbox=np.asarray([20, 20, 180, 180]),
                det_score=0.99,
                embedding=np.arange(1, 513, dtype=np.float32),
            )
        ]


class EnrollmentServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            shift = Shift(
                code="HC",
                name="Hành chính",
                start_time=time(8, 0),
                end_time=time(17, 0),
                late_grace_minutes=0,
                early_leave_grace_minutes=0,
                cross_day=False,
            )
            db.add(shift)
            db.flush()
            employee = Employee(
                employee_code="NV-ENROLL",
                full_name="Enrollment Test",
                shift_id=shift.id,
                status="PENDING_ENROLLMENT",
            )
            db.add(employee)
            db.commit()
            self.employee_id = employee.id
        self.original_interval = settings.ENROLLMENT_CAPTURE_INTERVAL_MS
        settings.ENROLLMENT_CAPTURE_INTERVAL_MS = 0

    def tearDown(self):
        settings.ENROLLMENT_CAPTURE_INTERVAL_MS = self.original_interval
        self.engine.dispose()

    def test_ten_samples_are_committed_with_centroid_and_activate_employee(self):
        service = EnrollmentService(
            store=EnrollmentSessionStore(), engine_factory=FakeEngine
        )
        session = service.start(self.employee_id)
        rng = np.random.default_rng(42)
        frame = rng.integers(0, 256, (200, 200, 3), dtype=np.uint8)

        with self.Session() as db:
            for _ in range(10):
                result = service.process_frame(db, session.session_id, frame)
                self.assertTrue(result[1])

            employee = db.get(Employee, self.employee_id)
            count = db.scalar(
                select(func.count(FaceEmbedding.id)).where(
                    FaceEmbedding.employee_id == self.employee_id
                )
            )
            centroid_count = db.scalar(
                select(func.count(FaceEmbedding.id)).where(
                    FaceEmbedding.employee_id == self.employee_id,
                    FaceEmbedding.is_centroid.is_(True),
                )
            )
            self.assertEqual(session.state, "COMPLETED")
            self.assertEqual(employee.status, "ACTIVE")
            self.assertEqual(count, 11)
            self.assertEqual(centroid_count, 1)

    def test_cancel_discards_in_memory_samples(self):
        service = EnrollmentService(
            store=EnrollmentSessionStore(), engine_factory=FakeEngine
        )
        session = service.start(self.employee_id)
        session.embeddings.append(np.ones(512, dtype=np.float32))
        cancelled = service.cancel(session.session_id)
        self.assertEqual(cancelled.state, "CANCELLED")
        self.assertEqual(cancelled.embeddings, [])


if __name__ == "__main__":
    unittest.main()
