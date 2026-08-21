import logging

from backend.app.core.config import settings
from backend.app.core.logging import log_extra
from backend.app.repositories.system_setting_repository import (
    SystemSettingRepository,
)


logger = logging.getLogger("face_attendance.settings")


class SettingDefinition:
    def __init__(self, key, value_type, group, label, description, minimum, maximum):
        self.key = key
        self.value_type = value_type
        self.group = group
        self.label = label
        self.description = description
        self.minimum = minimum
        self.maximum = maximum


# Only these keys may be edited at runtime. Anything not listed here stays in
# the environment, where changing it is a deployment decision.
EDITABLE_SETTINGS = {
    definition.key: definition
    for definition in (
        SettingDefinition(
            "FACE_SIMILARITY_THRESHOLD", "FLOAT", "Nhận diện",
            "Ngưỡng tương đồng khuôn mặt",
            "Càng cao càng chặt; dưới ngưỡng này sẽ không nhận diện được.",
            0.1, 1.0,
        ),
        SettingDefinition(
            "RECOGNITION_HOLD_SECONDS", "FLOAT", "Nhận diện",
            "Thời gian giữ khuôn mặt (giây)",
            "Số giây phải giữ khuôn mặt ổn định trước khi ghi nhận chấm công.",
            1, 30,
        ),
        SettingDefinition(
            "MIN_CHECKOUT_MINUTES", "INT", "Chấm công",
            "Thời gian tối thiểu trước check-out (phút)",
            "Chặn check-out lần đầu quá sớm sau khi check-in.",
            0, 1440,
        ),
        SettingDefinition(
            "MIN_PUNCH_INTERVAL_SECONDS", "INT", "Chấm công",
            "Khoảng cách tối thiểu giữa 2 lượt quét (giây)",
            "Tránh ghi trùng khi nhân viên đứng lâu trước kiosk.",
            0, 3600,
        ),
        SettingDefinition(
            "HALF_DAY_RATIO", "FLOAT", "Báo cáo",
            "Tỷ lệ tính nửa công",
            "Làm dưới tỷ lệ này so với giờ ca sẽ được tính nửa công (0.5HC).",
            0.1, 1.0,
        ),
    )
}


def _coerce(value, value_type):
    if value_type == "INT":
        return int(value)
    if value_type == "FLOAT":
        return float(value)
    if value_type == "BOOL":
        return str(value).strip().lower() in {"1", "true", "yes"}
    return value


class SettingsService:
    @staticmethod
    def get(db, key):
        """Read a business setting, falling back to the environment default."""
        definition = EDITABLE_SETTINGS.get(key)
        fallback = getattr(settings, key, None)

        if definition is None:
            return fallback

        row = SystemSettingRepository.get_by_key(db, key)
        if row is None:
            return fallback

        try:
            return _coerce(row.value, row.value_type)
        except (TypeError, ValueError):
            logger.warning(
                "Stored setting is not readable; using the environment default",
                extra=log_extra(
                    "setting_invalid", setting_key=key, stored_value=row.value
                ),
            )
            return fallback

    @staticmethod
    def get_int(db, key):
        return int(SettingsService.get(db, key))

    @staticmethod
    def get_float(db, key):
        return float(SettingsService.get(db, key))

    @staticmethod
    def list_all(db):
        stored = {row.key: row for row in SystemSettingRepository.list_all(db)}
        result = []

        for key, definition in EDITABLE_SETTINGS.items():
            row = stored.get(key)
            value = (
                _coerce(row.value, row.value_type)
                if row is not None
                else getattr(settings, key, None)
            )
            result.append(
                {
                    "key": key,
                    "value": str(value),
                    "value_type": definition.value_type,
                    "group": definition.group,
                    "label": definition.label,
                    "description": definition.description,
                    "minimum": definition.minimum,
                    "maximum": definition.maximum,
                    "updated_at": row.updated_at if row else None,
                }
            )

        return result

    @staticmethod
    def update(db, key, raw_value, admin_id):
        definition = EDITABLE_SETTINGS.get(key)
        if definition is None:
            raise ValueError("Tham số không được phép chỉnh sửa")

        try:
            value = _coerce(raw_value, definition.value_type)
        except (TypeError, ValueError):
            raise ValueError("Giá trị không đúng định dạng")

        if definition.value_type in {"INT", "FLOAT"}:
            if value < definition.minimum or value > definition.maximum:
                raise ValueError(
                    f"Giá trị phải nằm trong khoảng {definition.minimum} - "
                    f"{definition.maximum}"
                )

        SystemSettingRepository.upsert(
            db,
            key=key,
            value=str(value),
            value_type=definition.value_type,
            description=definition.description,
            admin_id=admin_id,
        )
        db.commit()

        logger.info(
            "System setting updated",
            extra=log_extra(
                "setting_updated",
                setting_key=key,
                new_value=str(value),
                admin_id=admin_id,
            ),
        )

        return value
