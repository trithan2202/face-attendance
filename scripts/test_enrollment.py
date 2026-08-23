import os
import re
import sys
import time

import cv2

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from face_engine import FaceEngine
from face_engine.quality import FaceQualityChecker


DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")

CAMERA_INDEX = 0
TARGET_SAMPLES = 5
CAPTURE_INTERVAL = 0.7


def sanitize_name(value):
    value = value.strip()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^a-zA-Z0-9_-]", "", value)

    return value


def draw_text(
    frame,
    text,
    position,
    color=(255, 255, 255),
    scale=0.7
):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        2,
        cv2.LINE_AA
    )


def main():
    employee_code = sanitize_name(
        input("Employee code: ")
    )

    employee_name = sanitize_name(
        input("Employee name: ")
    )

    if not employee_code or not employee_name:
        print("[ERROR] Invalid employee information")
        return

    person_name = f"{employee_code}_{employee_name}"

    person_dir = os.path.join(
        DATASET_DIR,
        person_name
    )

    os.makedirs(
        person_dir,
        exist_ok=True
    )

    print("[INFO] Loading InsightFace...")

    engine = FaceEngine()

    quality_checker = FaceQualityChecker(
        min_face_size=100,
        min_det_score=0.6,
        blur_threshold=80
    )

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    captured = 0
    last_capture_time = 0

    print("")
    print("[INFO] Look at the camera")
    print("[INFO] Move your head slightly between samples")
    print("[INFO] Press Q to cancel")
    print("")

    while captured < TARGET_SAMPLES:
        ret, frame = cap.read()

        if not ret:
            break

        faces = engine.detect(frame)

        status = "No face"
        status_color = (0, 0, 255)

        if len(faces) > 1:
            status = "Only one person allowed"

        elif len(faces) == 1:
            face = faces[0]

            valid, message = quality_checker.check(
                frame,
                face
            )

            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox

            if valid:
                status = message
                status_color = (0, 255, 0)

                current_time = time.time()

                if (
                    current_time - last_capture_time
                    >= CAPTURE_INTERVAL
                ):
                    captured += 1

                    file_path = os.path.join(
                        person_dir,
                        f"{captured:02d}.jpg"
                    )

                    cv2.imwrite(
                        file_path,
                        frame
                    )

                    last_capture_time = current_time

                    print(
                        f"[OK] Sample "
                        f"{captured}/{TARGET_SAMPLES}"
                    )

            else:
                status = message
                status_color = (0, 165, 255)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                status_color,
                2
            )

        draw_text(
            frame,
            f"Employee: {person_name}",
            (10, 30)
        )

        draw_text(
            frame,
            f"Samples: {captured}/{TARGET_SAMPLES}",
            (10, 60)
        )

        draw_text(
            frame,
            status,
            (10, 90),
            status_color
        )

        cv2.imshow(
            "Employee Enrollment",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Enrollment cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()

    if captured == TARGET_SAMPLES:
        print("")
        print("[SUCCESS] Enrollment completed")
        print(f"[INFO] Saved to: {person_dir}")
    else:
        print("")
        print(
            f"[WARNING] Enrollment incomplete: "
            f"{captured}/{TARGET_SAMPLES}"
        )


if __name__ == "__main__":
    main()