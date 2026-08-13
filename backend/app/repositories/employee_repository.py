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

from sqlalchemy import select

from backend.app.models import Employee


class EmployeeRepository:
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
            status="ACTIVE"
        )

        db.add(employee)
        db.flush()

        return employee