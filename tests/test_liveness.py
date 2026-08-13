import unittest

import numpy as np

from backend.app.core.config import settings
from backend.app.services.liveness import (
    BLINK,
    LEFT_CHEEK,
    LEFT_EYE,
    LivenessService,
    NOSE_TIP,
    RIGHT_CHEEK,
    RIGHT_EYE,
    TURN_LEFT,
    TURN_RIGHT,
)


def landmarks(eyes_open=True, nose_ratio=0.5):
    points = [(0.5, 0.5) for _ in range(478)]
    vertical = 0.04 if eyes_open else 0.004
    for indices, start_x in ((LEFT_EYE, 0.25), (RIGHT_EYE, 0.55)):
        values = (
            (start_x, 0.5),
            (start_x + 0.05, 0.5 - vertical),
            (start_x + 0.15, 0.5 - vertical),
            (start_x + 0.2, 0.5),
            (start_x + 0.15, 0.5 + vertical),
            (start_x + 0.05, 0.5 + vertical),
        )
        for index, value in zip(indices, values):
            points[index] = value
    points[LEFT_CHEEK] = (0.2, 0.5)
    points[RIGHT_CHEEK] = (0.8, 0.5)
    points[NOSE_TIP] = (0.2 + 0.6 * nose_ratio, 0.45)
    return points


class SequenceAnalyzer:
    def __init__(self, sequence):
        self.sequence = iter(sequence)

    def analyze(self, frame):
        return next(self.sequence)


class LivenessServiceTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.frame = rng.integers(0, 256, (240, 320, 3), dtype=np.uint8)

    def test_blink_requires_open_closed_open_sequence(self):
        analyzer = SequenceAnalyzer(
            [[[ *landmarks(True) ]], [[ *landmarks(False) ]], [[ *landmarks(True) ]]]
        )
        service = LivenessService(analyzer=analyzer, challenge_picker=lambda: BLINK)
        session = service.start()
        service.process_frame(session.session_id, self.frame)
        service.process_frame(session.session_id, self.frame)
        service.process_frame(session.session_id, self.frame)
        self.assertEqual(session.state, "PASSED")

    def test_turn_left_requires_consecutive_frames(self):
        sequence = [[[ *landmarks(nose_ratio=0.25) ]] for _ in range(3)]
        service = LivenessService(
            analyzer=SequenceAnalyzer(sequence), challenge_picker=lambda: TURN_LEFT
        )
        session = service.start()
        for _ in range(3):
            service.process_frame(session.session_id, self.frame)
        self.assertEqual(session.state, "PASSED")

    def test_turn_right_resets_progress_on_neutral_frame(self):
        sequence = [
            [[*landmarks(nose_ratio=0.75)]],
            [[*landmarks(nose_ratio=0.5)]],
        ]
        service = LivenessService(
            analyzer=SequenceAnalyzer(sequence), challenge_picker=lambda: TURN_RIGHT
        )
        session = service.start()
        service.process_frame(session.session_id, self.frame)
        self.assertEqual(session.progress, 1)
        service.process_frame(session.session_id, self.frame)
        self.assertEqual(session.progress, 0)
        self.assertEqual(session.state, "WAITING")

    def test_session_expires(self):
        service = LivenessService(challenge_picker=lambda: BLINK)
        session = service.start()
        session.created_at -= settings.LIVENESS_TIMEOUT_SECONDS + 1
        self.assertEqual(service.get(session.session_id).state, "FAILED")


if __name__ == "__main__":
    unittest.main()
