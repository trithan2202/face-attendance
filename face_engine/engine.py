from insightface.app import FaceAnalysis

from face_engine.recognizer import FaceRecognizer


class FaceEngine:
    def __init__(
        self,
        model_name="buffalo_l",
        providers=None,
        det_size=(640, 640)
    ):
        if providers is None:
            providers = ["CPUExecutionProvider"]

        self.app = FaceAnalysis(
            name=model_name,
            providers=providers
        )

        self.app.prepare(
            ctx_id=0,
            det_size=det_size
        )

    def detect(self, image):
        return self.app.get(image)

    def get_largest_face(self, image):
        faces = self.detect(image)

        if not faces:
            return None

        return max(
            faces,
            key=lambda face:
            (face.bbox[2] - face.bbox[0])
            * (face.bbox[3] - face.bbox[1])
        )

    def get_embedding(self, image):
        face = self.get_largest_face(image)

        if face is None:
            return None

        return FaceRecognizer.normalize(face.embedding)