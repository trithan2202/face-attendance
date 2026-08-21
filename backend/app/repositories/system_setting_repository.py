from sqlalchemy import select

from backend.app.models import SystemSetting


class SystemSettingRepository:
    @staticmethod
    def list_all(db):
        return list(db.scalars(select(SystemSetting).order_by(SystemSetting.key)))

    @staticmethod
    def get_by_key(db, key):
        return db.scalar(select(SystemSetting).where(SystemSetting.key == key))

    @staticmethod
    def upsert(db, key, value, value_type, description=None, admin_id=None):
        setting = SystemSettingRepository.get_by_key(db, key)

        if setting is None:
            setting = SystemSetting(
                key=key,
                value=value,
                value_type=value_type,
                description=description,
                updated_by_admin_id=admin_id,
            )
            db.add(setting)
        else:
            setting.value = value
            setting.value_type = value_type
            if description is not None:
                setting.description = description
            setting.updated_by_admin_id = admin_id

        db.flush()

        return setting
