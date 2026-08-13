import cv2


class CameraCapture:
    def __init__(self, source=0):
        self.source = source
        self.capture = None

    def open(self):
        self.capture = cv2.VideoCapture(
            self.source
        )

        if not self.capture.isOpened():
            raise RuntimeError(
                f"Cannot open camera: {self.source}"
            )

    def read(self):
        if self.capture is None:
            raise RuntimeError(
                "Camera is not opened"
            )

        return self.capture.read()

    def release(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None