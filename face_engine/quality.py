import cv2
import numpy as np


class FaceQualityChecker:
    def __init__(
        self,
        min_face_size=100,
        min_det_score=0.6,
        blur_threshold=80.0
    ):
        self.min_face_size = min_face_size
        self.min_det_score = min_det_score
        self.blur_threshold = blur_threshold

    def check(self, frame, face):
        x1, y1, x2, y2 = face.bbox.astype(int)

        width = x2 - x1
        height = y2 - y1

        if width < self.min_face_size or height < self.min_face_size:
            return False, "Face too small"

        if float(face.det_score) < self.min_det_score:
            return False, "Low detection score"

        h, w = frame.shape[:2]

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        face_crop = frame[y1:y2, x1:x2]

        if face_crop.size == 0:
            return False, "Invalid face crop"

        gray = cv2.cvtColor(
            face_crop,
            cv2.COLOR_BGR2GRAY
        )

        blur_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        if blur_score < self.blur_threshold:
            return False, f"Blurred ({blur_score:.0f})"

        return True, f"Good ({blur_score:.0f})"