import cv2

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.repositories import FaceRepository
from face_engine import FaceEngine, FaceMatcher


def load_face_cache():
    db = get_db_session()

    try:
        employees = (
            FaceRepository.get_centroid_embeddings(
                db
            )
        )
    finally:
        db.close()

    known_faces = {
        code: data["embedding"]
        for code, data in employees.items()
    }

    metadata = {
        code: data
        for code, data in employees.items()
    }

    return known_faces, metadata


def draw_label(
    frame,
    text,
    x,
    y,
    color
):
    cv2.putText(
        frame,
        text,
        (x, max(y - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA
    )


def main():
    print("[INFO] Loading employee cache...")

    known_faces, metadata = (
        load_face_cache()
    )

    print(
        f"[INFO] Loaded "
        f"{len(known_faces)} employees"
    )

    if not known_faces:
        print(
            "[WARNING] No enrolled employees"
        )

    print("[INFO] Loading InsightFace...")

    engine = FaceEngine()

    matcher = FaceMatcher(
        threshold=(
            settings.FACE_SIMILARITY_THRESHOLD
        )
    )

    cap = cv2.VideoCapture(
        settings.CAMERA_INDEX
    )

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            faces = engine.detect(frame)

            for face in faces:
                x1, y1, x2, y2 = (
                    face.bbox.astype(int)
                )

                employee_code, score = (
                    matcher.match(
                        face.embedding,
                        known_faces
                    )
                )

                if employee_code is None:
                    label = (
                        f"Unknown | {score:.3f}"
                    )
                    color = (0, 0, 255)

                else:
                    employee = metadata[
                        employee_code
                    ]

                    label = (
                        f"{employee_code} - "
                        f"{employee['full_name']} "
                        f"| {score:.3f}"
                    )

                    color = (0, 255, 0)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                draw_label(
                    frame,
                    label,
                    x1,
                    y1,
                    color
                )

            cv2.imshow(
                "DB Face Recognition",
                frame
            )

            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()