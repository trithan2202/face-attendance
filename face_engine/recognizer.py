import numpy as np


class FaceRecognizer:
    @staticmethod
    def normalize(embedding):
        embedding = np.asarray(embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding)

        if norm == 0:
            return embedding

        return embedding / norm

    @classmethod
    def create_centroid(cls, embeddings):
        if not embeddings:
            raise ValueError("Embeddings list is empty")

        embeddings = np.asarray([
            cls.normalize(embedding)
            for embedding in embeddings
        ])

        centroid = np.mean(embeddings, axis=0)

        return cls.normalize(centroid)