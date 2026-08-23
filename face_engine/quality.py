import cv2
import numpy as np


class FaceQualityChecker:
    def __init__(
        self,
        min_face_size=100,
        min_det_score=0.6,
        blur_threshold=80.0,
        min_brightness=45.0,
        max_brightness=215.0
    ):
        self.min_face_size = min_face_size
        self.min_det_score = min_det_score
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness

    def check(self, frame, face):
        x1, y1, x2, y2 = face.bbox.astype(int)

        width = x2 - x1
        height = y2 - y1

        if width < self.min_face_size or height < self.min_face_size:
            return False, "Khuôn mặt quá nhỏ"

        if float(face.det_score) < self.min_det_score:
            return False, "Độ tin cậy phát hiện khuôn mặt quá thấp"

        h, w = frame.shape[:2]

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        face_crop = frame[y1:y2, x1:x2]

        if face_crop.size == 0:
            return False, "Vùng khuôn mặt không hợp lệ"

        gray = cv2.cvtColor(
            face_crop,
            cv2.COLOR_BGR2GRAY
        )

        # Đo trên khung hình gốc chứ không phải ảnh đã tiền xử lý: tiền xử lý
        # cứu được ánh sáng lệch ở mức vừa phải, nhưng quá tối thì ảnh chỉ còn
        # nhiễu và quá chói thì chi tiết đã mất hẳn - cả hai đều không nên đưa
        # vào bộ mẫu đăng ký.
        brightness = float(np.mean(gray))

        if brightness < self.min_brightness:
            return False, f"Ánh sáng quá tối ({brightness:.0f}), hãy bật thêm đèn"

        if brightness > self.max_brightness:
            return False, f"Ánh sáng quá chói ({brightness:.0f}), tránh ngược sáng"

        blur_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        if blur_score < self.blur_threshold:
            return False, f"Hình ảnh bị mờ ({blur_score:.0f})"

        return True, f"Chất lượng đạt ({blur_score:.0f})"
