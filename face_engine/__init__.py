__all__ = [
    "FaceEngine",
    "FaceMatcher",
    "FaceQualityChecker",
    "FaceRecognizer",
    "FramePreprocessor",
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
    if name == "FramePreprocessor":
        from .preprocess import FramePreprocessor

        return FramePreprocessor
    raise AttributeError(name)
