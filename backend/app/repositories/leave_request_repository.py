from sqlalchemy import select

from backend.app.models import AdminUser, Employee, LeaveRequest


class LeaveRequestRepository:
    @staticmethod
    def list(db, employee_id=None, status=None, date_from=None, date_to=None):
        stmt = (
            select(LeaveRequest, Employee, AdminUser.username)
            .join(Employee, Employee.id == LeaveRequest.employee_id)
            .join(AdminUser, AdminUser.id == LeaveRequest.created_by_admin_id)
            .order_by(LeaveRequest.start_date.desc(), LeaveRequest.id.desc())
        )
        if employee_id:
            stmt = stmt.where(LeaveRequest.employee_id == employee_id)
        if status:
            stmt = stmt.where(LeaveRequest.status == status)
        if date_from:
            stmt = stmt.where(LeaveRequest.end_date >= date_from)
        if date_to:
            stmt = stmt.where(LeaveRequest.start_date <= date_to)
        return list(db.execute(stmt).all())

    @staticmethod
    def get_by_id(db, leave_id):
        return db.get(LeaveRequest, leave_id)

    @staticmethod
    def get_detail(db, leave_id, for_update=False):
        stmt = (
            select(LeaveRequest, Employee, AdminUser.username)
            .join(Employee, Employee.id == LeaveRequest.employee_id)
            .join(AdminUser, AdminUser.id == LeaveRequest.created_by_admin_id)
            .where(LeaveRequest.id == leave_id)
        )
        if for_update:
            stmt = stmt.with_for_update(of=LeaveRequest)
        return db.execute(stmt).first()

    @staticmethod
    def find_overlapping(db, employee_id, start_date, end_date, exclude_id=None):
        stmt = select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(("PENDING", "APPROVED")),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        if exclude_id:
            stmt = stmt.where(LeaveRequest.id != exclude_id)
        return db.scalar(stmt)

    @staticmethod
    def create(
        db,
        employee_id,
        leave_type,
        start_date,
        end_date,
        reason,
        created_by_admin_id,
    ):
        leave = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="PENDING",
            created_by_admin_id=created_by_admin_id,
        )

        db.add(leave)
        db.flush()

        return leave

    @staticmethod
    def delete(db, leave):
        db.delete(leave)
        db.flush()
