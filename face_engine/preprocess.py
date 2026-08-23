import cv2
import numpy as np


class FramePreprocessor:
    """Chuẩn hóa ánh sáng của khung hình trước khi đưa vào mô hình.

    Ba bước, chạy theo thứ tự từ tổng thể đến cục bộ:

    1. Hiệu chỉnh gamma - kéo độ sáng trung bình của khung hình về mức mục
       tiêu. Xử lý được cả phòng thiếu sáng (ảnh tối) lẫn ngược sáng cửa sổ
       (ảnh cháy trắng).
    2. Khử nhiễu nhẹ - chỉ chạy khi khung hình gốc quá tối, vì ảnh tối luôn
       nhiều nhiễu và bước CLAHE phía sau sẽ khuếch đại nhiễu đó lên.
    3. CLAHE trên kênh L (LAB) - cân bằng sáng cục bộ theo từng ô nhỏ, nên
       nửa mặt bị bóng đổ vẫn hiện rõ chi tiết mà nửa còn lại không bị cháy.
       Chỉ tác động lên kênh sáng, giữ nguyên màu da ở kênh a/b.
    """

    def __init__(
        self,
        enabled=True,
        clip_limit=2.0,
        tile_grid_size=8,
        target_brightness=125.0,
        brightness_tolerance=25.0,
        dark_threshold=70.0,
        gamma_range=(0.4, 2.5),
    ):
        self.enabled = enabled
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.target_brightness = target_brightness
        self.brightness_tolerance = brightness_tolerance
        self.dark_threshold = dark_threshold
        self.gamma_range = gamma_range
        self._clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(tile_grid_size, tile_grid_size),
        )

    @classmethod
    def from_settings(cls, settings):
        """Dựng bộ tiền xử lý từ cấu hình runtime (duck-typing, không import ngược)."""
        return cls(
            enabled=settings.IMAGE_PREPROCESS_ENABLED,
            clip_limit=settings.IMAGE_CLAHE_CLIP_LIMIT,
            tile_grid_size=settings.IMAGE_CLAHE_TILE_GRID,
            target_brightness=settings.IMAGE_TARGET_BRIGHTNESS,
            brightness_tolerance=settings.IMAGE_BRIGHTNESS_TOLERANCE,
        )

    @staticmethod
    def brightness(frame):
        """Độ sáng trung bình 0..255 của khung hình."""
        if frame is None or getattr(frame, "size", 0) == 0:
            return 0.0
        if frame.ndim == 2:
            gray = frame
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    def enhance(self, frame):
        """Trả về (khung hình đã xử lý, thông số đo được).

        Kích thước ảnh không đổi nên tọa độ bounding box của mô hình vẫn khớp
        với khung hình gốc mà giao diện đang hiển thị.
        """
        stats = {
            "enabled": self.enabled,
            "brightness_before": 0.0,
            "brightness_after": 0.0,
            "gamma": 1.0,
            "clahe": False,
            "denoised": False,
        }
        if frame is None or getattr(frame, "size", 0) == 0:
            return frame, stats

        before = self.brightness(frame)
        stats["brightness_before"] = round(before, 2)
        stats["brightness_after"] = stats["brightness_before"]
        if not self.enabled or frame.ndim != 3 or frame.shape[2] != 3:
            return frame, stats

        result = frame
        gamma = self._gamma_for(before)
        if gamma != 1.0:
            result = self._apply_gamma(result, gamma)
            stats["gamma"] = round(gamma, 3)

        if before < self.dark_threshold:
            result = cv2.bilateralFilter(result, 5, 50, 50)
            stats["denoised"] = True

        result = self._apply_clahe(result)
        stats["clahe"] = True
        stats["brightness_after"] = round(self.brightness(result), 2)
        return result, stats

    def _gamma_for(self, brightness):
        """Gamma đưa độ sáng trung bình về gần mức mục tiêu.

        Bỏ qua khi khung hình đã nằm trong dải chấp nhận được, để không làm
        biến dạng ảnh vốn đã đủ sáng.
        """
        if brightness <= 1.0 or brightness >= 254.0:
            return 1.0
        if abs(brightness - self.target_brightness) <= self.brightness_tolerance:
            return 1.0
        gamma = np.log(self.target_brightness / 255.0) / np.log(brightness / 255.0)
        low, high = self.gamma_range
        return float(min(high, max(low, gamma)))

    @staticmethod
    def _apply_gamma(frame, gamma):
        table = np.array(
            [((value / 255.0) ** gamma) * 255 for value in range(256)],
            dtype=np.uint8,
        )
        return cv2.LUT(frame, table)

    def _apply_clahe(self, frame):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lightness, a_channel, b_channel = cv2.split(lab)
        lightness = self._clahe.apply(lightness)
        return cv2.cvtColor(
            cv2.merge((lightness, a_channel, b_channel)), cv2.COLOR_LAB2BGR
        )
