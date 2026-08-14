import unittest
from datetime import time
from types import SimpleNamespace

import numpy as np
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401
from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.core.embedding_codec import encode_embedding
from backend.app.models import (
    AttendanceDaily,
    AttendanceEvent,
    Employee,
    FaceEmbedding,
    Shift,
)
from backend.app.services.recognition import RecognitionService


class FakeRecognitionEngine:
    embedding = np.arange(1, 513, dtype=np.float32)

    def detect(self, frame):
        return [
            SimpleNamespace(
                embedding=self.embedding,
                det_score=0.99,
                bbox=np.asarray([10, 10, 100, 100]),
            )
        ]


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class RecognitionServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.Session() as db:
            shift = Shift(
                code="HC",
                name="Hành chính",
                start_time=time(8),
                end_time=time(17),
                late_grace_minutes=10,
                early_leave_grace_minutes=10,
                cross_day=False,
            )
            db.add(shift)
            db.flush()
            employee = Employee(
                employee_code="NV-RECOGNITION",
                full_name="Recognition Test",
                shift_id=shift.id,
                status="ACTIVE",
            )
            db.add(employee)
            db.flush()
            normalized = FakeRecognitionEngine.embedding
            normalized = normalized / np.linalg.norm(normalized)
            db.add(
                FaceEmbedding(
                    employee_id=employee.id,
                    embedding=encode_embedding(normalized),
                    is_centroid=True,
                    model_name="buffalo_l",
                )
            )
            db.commit()
        self.original_hold = settings.RECOGNITION_HOLD_SECONDS
        self.original_gap = settings.RECOGNITION_MAX_FRAME_GAP_SECONDS
        settings.RECOGNITION_HOLD_SECONDS = 3
        settings.RECOGNITION_MAX_FRAME_GAP_SECONDS = 1

    def tearDown(self):
        settings.RECOGNITION_HOLD_SECONDS = self.original_hold
        settings.RECOGNITION_MAX_FRAME_GAP_SECONDS = self.original_gap
        self.engine.dispose()

    def test_three_continuous_seconds_create_check_in(self):
        clock = FakeClock()
        service = RecognitionService(engine_factory=FakeRecognitionEngine, clock=clock)
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        with self.Session() as db:
            session = service.start(db)
            for _ in range(3):
                service.process_frame(db, session.session_id, frame)
                self.assertEqual(session.state, "RECOGNIZING")
                clock.advance(1)
            service.process_frame(db, session.session_id, frame)
            self.assertEqual(session.state, "COMPLETED")
            self.assertEqual(session.event_type, "CHECK_IN")
            self.assertEqual(session.stable_seconds, 3)
            self.assertEqual(db.scalar(select(func.count(AttendanceEvent.id))), 1)
            self.assertEqual(db.scalar(select(func.count(AttendanceDaily.id))), 1)

    def test_long_frame_gap_restarts_three_second_timer(self):
        clock = FakeClock()
        service = RecognitionService(engine_factory=FakeRecognitionEngine, clock=clock)
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        with self.Session() as db:
            session = service.start(db)
            service.process_frame(db, session.session_id, frame)
            clock.advance(1.5)
            service.process_frame(db, session.session_id, frame)
            self.assertEqual(session.state, "RECOGNIZING")
            self.assertEqual(session.stable_seconds, 0)

    def test_second_scan_too_soon_returns_cooldown(self):
        clock = FakeClock()
        service = RecognitionService(engine_factory=FakeRecognitionEngine, clock=clock)
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        with self.Session() as db:
            first = service.start(db)
            for _ in range(4):
                service.process_frame(db, first.session_id, frame)
                clock.advance(1)
            second = service.start(db)
            for _ in range(4):
                service.process_frame(db, second.session_id, frame)
                clock.advance(1)
            self.assertEqual(second.state, "COOLDOWN")
            self.assertIsNone(second.event_type)
            self.assertEqual(db.scalar(select(func.count(AttendanceEvent.id))), 1)


if __name__ == "__main__":
    unittest.main()
