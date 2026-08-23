import time

import cv2

from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.repositories.face_repository import FaceRepository
from face_engine import (
    FaceEngine,
    FaceQualityChecker,
    FaceRecognizer
)
from backend.app.repositories.shift_repository import ShiftRepository

TARGET_SAMPLES = 5
CAPTURE_INTERVAL = 0.7


def draw_text(
    frame,
    text,
    position,
    color=(255, 255, 255)
):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA
    )


def main():
    employee_code = input(
        "Employee code: "
    ).strip()

    full_name = input(
        "Full name: "
    ).strip()

    department = input(
        "Department: "
    ).strip() or None

    if not employee_code or not full_name:
        print("[ERROR] Employee information is required")
        return

    shift_code = input("Shift code [HC]: ").strip() or "HC"
    
    # Phải khởi tạo db session sớm để có thể truy vấn DB
    db = get_db_session()

    try:
        shift = ShiftRepository.get_by_code(
            db,
            shift_code
        )
        
        if shift is None:
            raise ValueError(
                f"Shift not found: {shift_code}"
            )

        employee = EmployeeRepository.create(
            db,
            employee_code=employee_code,
            full_name=full_name,
            shift_id=shift.id,
            department=department
        )
        # Commit sớm nếu hàm create chưa tự động commit
        db.commit() 
        
    except Exception as e:
        print(f"[ERROR] {e}")
        db.rollback()
        db.close()
        return
    
    print("[INFO] Loading InsightFace...")

    engine = FaceEngine()

    quality_checker = FaceQualityChecker(
        min_face_size=100,
        min_det_score=0.6,
        blur_threshold=80
    )

    cap = cv2.VideoCapture(
        settings.CAMERA_INDEX
    )

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    embeddings = []
    last_capture_time = 0

    try:
        while len(embeddings) < TARGET_SAMPLES:
            ret, frame = cap.read()

            if not ret:
                break

            faces = engine.detect(frame)

            status = "No face"
            color = (0, 0, 255)

            if len(faces) > 1:
                status = "Only one face allowed"

            elif len(faces) == 1:
                face = faces[0]

                valid, message = quality_checker.check(
                    frame,
                    face
                )

                x1, y1, x2, y2 = (
                    face.bbox.astype(int)
                )

                if valid:
                    color = (0, 255, 0)
                    status = message

                    now = time.time()

                    if (
                        now - last_capture_time
                        >= CAPTURE_INTERVAL
                    ):
                        embedding = (
                            FaceRecognizer.normalize(
                                face.embedding
                            )
                        )

                        embeddings.append(
                            embedding
                        )

                        last_capture_time = now

                        print(
                            f"[OK] Sample "
                            f"{len(embeddings)}"
                            f"/{TARGET_SAMPLES}"
                        )
                else:
                    color = (0, 165, 255)
                    status = message

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

            draw_text(
                frame,
                f"Employee: {employee_code}",
                (10, 30)
            )

            draw_text(
                frame,
                (
                    f"Samples: "
                    f"{len(embeddings)}"
                    f"/{TARGET_SAMPLES}"
                ),
                (10, 60)
            )

            draw_text(
                frame,
                status,
                (10, 90),
                color
            )

            cv2.imshow(
                "Enrollment",
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

    if len(embeddings) < TARGET_SAMPLES:
        print("[WARNING] Enrollment incomplete")
        return

    centroid = FaceRecognizer.create_centroid(
        embeddings
    )

    # db = get_db_session()

    # try:
    #     employee, created = (
    #         EmployeeRepository.get_or_create(
    #             db,
    #             employee_code,
    #             full_name,
    #             department
    #         )
    #     )
    try:
        FaceRepository.delete_employee_embeddings(
            db,
            employee.id
        )

        # for embedding in embeddings:
        #     FaceRepository.add_embedding(
        #         db,
        #         employee.id,
        #         embedding,
        #         embedding_type="sample"
        #     )

        for index, embedding in enumerate(
            embeddings,
            start=1
        ):
            FaceRepository.add_embedding(
                db,
                employee.id,
                embedding,
                sample_index=index,
                is_centroid=False
            )

        FaceRepository.add_embedding(
            db,
            employee.id,
            centroid,
            sample_index=None,
            is_centroid=True
        )

        db.commit()

        print("")
        print("[SUCCESS] Enrollment completed")
        print(
            f"[INFO] Employee: "
            f"{employee.employee_code}"
        )
        print(
            f"[INFO] Stored samples: "
            f"{len(embeddings)}"
        )
        print("[INFO] Stored centroid: 1")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
