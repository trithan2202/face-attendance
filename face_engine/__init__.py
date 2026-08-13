__all__ = [
    "FaceEngine",
    "FaceMatcher",
    "FaceQualityChecker",
    "FaceRecognizer",
]


def __getattr__(name):
    if name == "FaceEngine":
        from .engine import FaceEngine

        return FaceEngine
    if name == "FaceMatcher":
        from .matcher import FaceMatcher

        return FaceMatcher
    if name == "FaceQualityChecker":
        from .quality import FaceQualityChecker

        return FaceQualityChecker
    if name == "FaceRecognizer":
        from .recognizer import FaceRecognizer

        return FaceRecognizer
    raise AttributeError(name)
