import numpy as np


def encode_embedding(embedding):
    return np.asarray(
        embedding,
        dtype=np.float32
    ).tobytes()


def decode_embedding(data):
    return np.frombuffer(
        data,
        dtype=np.float32
    ).copy()