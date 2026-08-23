from insightface.app import FaceAnalysis

from face_engine.preprocess import FramePreprocessor
from face_engine.recognizer import FaceRecognizer


class FaceEngine:
    def __init__(
        self,
        model_name="buffalo_l",
        providers=None,
        det_size=(640, 640),
        preprocessor=None
    ):
        if providers is None:
            providers = ["CPUExecutionProvider"]

        # Tiền xử lý đặt ở đây để cả luồng nhận diện lẫn luồng đăng ký khuôn
        # mặt dùng chung một cách chuẩn hóa ảnh, tránh lệch phân bố dữ liệu
        # giữa embedding lúc đăng ký và embedding lúc chấm công.
        self.preprocessor = preprocessor or FramePreprocessor()
        self.last_preprocess_stats = {}

        self.app = FaceAnalysis(
            name=model_name,
            providers=providers
        )

        self.app.prepare(
            ctx_id=0,
            det_size=det_size
        )

    def detect(self, image):
        prepared, stats = self.preprocessor.enhance(image)
        self.last_preprocess_stats = stats

        return self.app.get(prepared)

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
