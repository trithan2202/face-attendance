from sqlalchemy import func, select

from backend.app.models import Department, Employee


class DepartmentRepository:
    @staticmethod
    def list_all(db):
        return list(db.scalars(select(Department).order_by(Department.code)))

    @staticmethod
    def get_by_id(db, department_id):
        return db.get(Department, department_id)

    @staticmethod
    def get_by_code(db, code):
        return db.scalar(select(Department).where(Department.code == code))

    @staticmethod
    def create(db, code, name, manager_name=None):
        department = Department(
            code=code,
            name=name,
            manager_name=manager_name,
        )

        db.add(department)
        db.flush()

        return department

    @staticmethod
    def update(db, department, **values):
        for field, value in values.items():
            setattr(department, field, value)
        db.flush()
        return department

    @staticmethod
    def employee_count(db, department_id):
        return db.scalar(
            select(func.count(Employee.id)).where(
                Employee.department_id == department_id
            )
        ) or 0

    @staticmethod
    def delete(db, department):
        db.delete(department)
        db.flush()
