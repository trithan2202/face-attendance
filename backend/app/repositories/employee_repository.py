# from sqlalchemy import select

# from backend.app.models import Employee


# class EmployeeRepository:
#     @staticmethod
#     def get_by_code(db, employee_code):
#         stmt = select(Employee).where(
#             Employee.employee_code == employee_code
#         )

#         return db.scalar(stmt)

#     @staticmethod
#     def get_by_id(db, employee_id):
#         return db.get(
#             Employee,
#             employee_id
#         )

#     @staticmethod
#     def create(
#         db,
#         employee_code,
#         full_name,
#         department=None
#     ):
#         employee = Employee(
#             employee_code=employee_code,
#             full_name=full_name,
#             department=department
#         )

#         db.add(employee)
#         db.flush()

#         return employee

#     @staticmethod
#     def get_or_create(
#         db,
#         employee_code,
#         full_name,
#         department=None
#     ):
#         employee = EmployeeRepository.get_by_code(
#             db,
#             employee_code
#         )

#         if employee:
#             return employee, False

#         employee = EmployeeRepository.create(
#             db,
#             employee_code,
#             full_name,
#             department
#         )

#         return employee, True

from sqlalchemy import func, or_, select

from backend.app.models import Employee, FaceEmbedding


class EmployeeRepository:
    @staticmethod
    def list(db, search=None, status=None):
        stmt = select(Employee).order_by(Employee.employee_code)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Employee.employee_code.ilike(pattern),
                    Employee.full_name.ilike(pattern),
                    Employee.department.ilike(pattern),
                )
            )
        if status:
            stmt = stmt.where(Employee.status == status)
        return list(db.scalars(stmt))

    @staticmethod
    def get_by_id(db, employee_id):
        return db.get(Employee, employee_id)

    @staticmethod
    def get_by_code(db, employee_code):
        return db.scalar(
            select(Employee).where(
                Employee.employee_code
                == employee_code
            )
        )

    @staticmethod
    def create(
        db,
        employee_code,
        full_name,
        shift_id,
        email=None,
        phone=None,
        department=None
    ):
        employee = Employee(
            employee_code=employee_code,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            shift_id=shift_id,
            status="PENDING_ENROLLMENT"
        )

        db.add(employee)
        db.flush()

        return employee

    @staticmethod
    def update(db, employee, **values):
        for field, value in values.items():
            setattr(employee, field, value)
        db.flush()
        return employee

    @staticmethod
    def enrollment_stats(db, employee_id):
        sample_count = db.scalar(
            select(func.count(FaceEmbedding.id)).where(
                FaceEmbedding.employee_id == employee_id,
                FaceEmbedding.is_centroid.is_(False),
            )
        ) or 0
        has_centroid = bool(
            db.scalar(
                select(func.count(FaceEmbedding.id)).where(
                    FaceEmbedding.employee_id == employee_id,
                    FaceEmbedding.is_centroid.is_(True),
                )
            )
        )
        return sample_count, has_centroid
