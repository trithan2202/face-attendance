import numpy as np

from face_engine.recognizer import FaceRecognizer


class FaceMatcher:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    @staticmethod
    def cosine_similarity(embedding1, embedding2):
        embedding1 = FaceRecognizer.normalize(embedding1)
        embedding2 = FaceRecognizer.normalize(embedding2)

        return float(np.dot(embedding1, embedding2))

    def match(self, query_embedding, known_faces):
        if not known_faces:
            return None, -1.0

        best_name = None
        best_score = -1.0

        for name, embedding in known_faces.items():
            score = self.cosine_similarity(
                query_embedding,
                embedding
            )

            if score > best_score:
                best_score = score
                best_name = name

        if best_score < self.threshold:
            return None, best_score

        return best_name, best_score