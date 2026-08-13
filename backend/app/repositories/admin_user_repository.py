from sqlalchemy import select

from backend.app.models import AdminUser


class AdminUserRepository:
    @staticmethod
    def get_by_id(db, admin_id: int):
        return db.get(AdminUser, admin_id)

    @staticmethod
    def get_by_username(db, username: str):
        return db.scalar(select(AdminUser).where(AdminUser.username == username))

    @staticmethod
    def create(db, username: str, password_hash: str):
        admin = AdminUser(username=username, password_hash=password_hash, is_active=True)
        db.add(admin)
        db.flush()
        return admin
