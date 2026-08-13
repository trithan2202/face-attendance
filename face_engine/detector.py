class FaceDetector:
    def __init__(self, face_app):
        self.face_app = face_app

    def detect(self, frame):
        return self.face_app.get(frame)