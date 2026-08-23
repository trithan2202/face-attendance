import logging
import threading
import time

from backend.app.core.config import settings
from backend.app.core.logging import log_extra


logger = logging.getLogger("face_attendance.face_engine")

_engine = None
_lock = threading.Lock()


def get_face_engine():
    """Trả về FaceEngine dùng chung cho cả nhận diện lẫn đăng ký khuôn mặt.

    Bộ mô hình buffalo_l nặng khoảng 280 MB. Trước đây mỗi service tự dựng
    một engine riêng nên mô hình bị nạp hai lần: người dùng chờ nạp một lần ở
    màn hình đăng ký, rồi lại chờ thêm một lần nữa ở lần chấm công đầu tiên,
    và tiến trình giữ gấp đôi bộ nhớ cần thiết.
    """
    global _engine

    if _engine is not None:
        return _engine

    with _lock:
        if _engine is None:
            from face_engine.engine import FaceEngine
            from face_engine.preprocess import FramePreprocessor

            logger.info(
                "Loading face recognition model",
                extra=log_extra("face_engine_loading"),
            )
            started = time.perf_counter()
            engine = FaceEngine(
                preprocessor=FramePreprocessor.from_settings(settings)
            )
            _engine = engine
            logger.info(
                "Face recognition model ready",
                extra=log_extra(
                    "face_engine_ready",
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                ),
            )

    return _engine


def warm_up():
    """Nạp trước mô hình lúc khởi động, chạy ở luồng nền.

    Nếu để mô hình nạp lười ở request đầu tiên thì request đó phải giữ khóa
    suốt vài phút (lần đầu còn phải tải mô hình về), khiến mọi khung hình gửi
    lên đều xếp hàng và phiên nhận diện hết hạn trước khi tới lượt.
    """
    try:
        get_face_engine()
    except Exception:
        logger.exception(
            "Face engine warm-up failed",
            extra=log_extra("face_engine_warmup_failed"),
        )
