import os
import sys

import cv2

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from face_engine import FaceEngine, FaceMatcher, FaceRecognizer


DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")

CAMERA_INDEX = 0
SIMILARITY_THRESHOLD = 0.5

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
)


def load_known_faces(engine):
    known_faces = {}

    if not os.path.exists(DATASET_DIR):
        raise FileNotFoundError(
            f"Dataset directory not found: {DATASET_DIR}"
        )

    person_dirs = sorted(os.listdir(DATASET_DIR))

    for person_name in person_dirs:
        person_path = os.path.join(
            DATASET_DIR,
            person_name
        )

        if not os.path.isdir(person_path):
            continue

        embeddings = []

        for file_name in sorted(os.listdir(person_path)):
            if not file_name.lower().endswith(IMAGE_EXTENSIONS):
                continue

            image_path = os.path.join(
                person_path,
                file_name
            )

            image = cv2.imread(image_path)

            if image is None:
                print(f"[SKIP] Cannot read: {image_path}")
                continue

            embedding = engine.get_embedding(image)

            if embedding is None:
                print(f"[SKIP] No face: {image_path}")
                continue

            embeddings.append(embedding)

        if not embeddings:
            print(f"[SKIP] No valid embeddings: {person_name}")
            continue

        centroid = FaceRecognizer.create_centroid(
            embeddings
        )

        known_faces[person_name] = centroid

        print(
            f"[OK] {person_name}: "
            f"{len(embeddings)} samples"
        )

    return known_faces


def draw_label(
    frame,
    text,
    x,
    y,
    color
):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.65
    thickness = 2

    (width, height), _ = cv2.getTextSize(
        text,
        font,
        scale,
        thickness
    )

    y = max(y, height + 10)

    cv2.rectangle(
        frame,
        (x, y - height - 10),
        (x + width + 10, y),
        color,
        -1
    )

    cv2.putText(
        frame,
        text,
        (x + 5, y - 5),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA
    )


def main():
    print("[INFO] Loading InsightFace...")

    engine = FaceEngine()

    matcher = FaceMatcher(
        threshold=SIMILARITY_THRESHOLD
    )

    print("[INFO] Loading dataset...")

    known_faces = load_known_faces(engine)

    if not known_faces:
        print("[ERROR] No known faces found.")
        return

    print(
        f"[INFO] Loaded {len(known_faces)} people"
    )

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        faces = engine.detect(frame)

        for face in faces:
            bbox = face.bbox.astype(int)

            x1, y1, x2, y2 = bbox

            name, score = matcher.match(
                face.embedding,
                known_faces
            )

            if name is None:
                label = f"Unknown | {score:.3f}"
                color = (0, 0, 255)
            else:
                label = f"{name} | {score:.3f}"
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

        cv2.putText(
            frame,
            f"Threshold: {SIMILARITY_THRESHOLD:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.imshow(
            "InsightFace Recognition",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()