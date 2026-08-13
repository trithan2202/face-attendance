from backend.app.core.database import get_db_session
from backend.app.repositories.face_repository import FaceRepository


class EmbeddingCache:
    def __init__(self):
        self.known_faces = {}
        self.metadata = {}

    def refresh(self):
        db = get_db_session()

        try:
            data = FaceRepository.get_centroids(
                db
            )
        finally:
            db.close()

        self.known_faces = {
            code: item["embedding"]
            for code, item in data.items()
        }

        self.metadata = data

        return len(self.known_faces)

    def get_employee(self, employee_code):
        return self.metadata.get(
            employee_code
        )