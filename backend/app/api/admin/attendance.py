from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.schemas import (
    AttendanceAdjustmentRequest,
    AttendanceAdjustmentResponse,
    AttendanceDailyResponse,
    AttendanceDetailResponse,
)
from backend.app.services.attendance_adjustment import AttendanceAdjustmentService
from backend.app.services.attendance_export import (
    XLSX_MEDIA_TYPE,
    build_daily_workbook,
    build_monthly_report,
)


router = APIRouter(prefix="/admin/attendance", tags=["admin-attendance"])


def _daily_response(daily, employee, shift):
    return AttendanceDailyResponse(
        id=daily.id,
        employee_id=employee.id,
        employee_code=employee.employee_code,
        full_name=employee.full_name,
        department=employee.department,
        shift_id=shift.id,
        shift_code=shift.code,
        work_date=daily.work_date,
        first_check_in=daily.first_check_in,
        last_check_out=daily.last_check_out,
        worked_minutes=daily.worked_minutes,
        late_minutes=daily.late_minutes,
        early_leave_minutes=daily.early_leave_minutes,
        overtime_minutes=daily.overtime_minutes,
        status=daily.status,
        is_late=daily.is_late,
        is_early_leave=daily.is_early_leave,
        is_overtime=daily.is_overtime,
    )


@router.get("", response_model=list[AttendanceDailyResponse])
def list_attendance(
    date_from: date | None = None,
    date_to: date | None = None,
    employee_id: int | None = None,
    department: str | None = Query(default=None, max_length=255),
    attendance_status: str | None = Query(default=None, alias="status", max_length=30),
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="Ngày bắt đầu phải trước ngày kết thúc")
    rows = AttendanceRepository.list_daily(
        db, date_from, date_to, employee_id, department, attendance_status
    )
    return [_daily_response(*row) for row in rows]


@router.get("/export.xlsx")
def export_attendance_excel(
    date_from: date | None = None,
    date_to: date | None = None,
    employee_id: int | None = None,
    department: str | None = Query(default=None, max_length=255),
    attendance_status: str | None = Query(default=None, alias="status", max_length=30),
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="Ngày bắt đầu phải trước ngày kết thúc")
    rows = AttendanceRepository.list_daily(
        db, date_from, date_to, employee_id, department, attendance_status
    )
    output = build_daily_workbook(rows, date_from=date_from, date_to=date_to)
    return StreamingResponse(
        output,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": "attachment; filename=attendance-report.xlsx"
        },
    )


@router.get("/export-monthly.xlsx")
def export_monthly_attendance_excel(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    employee_id: int | None = None,
    department: str | None = Query(default=None, max_length=255),
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    output = build_monthly_report(
        db,
        year,
        month,
        employee_id=employee_id,
        department=department,
    )
    return StreamingResponse(
        output,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": (
                f"attachment; filename=attendance-monthly-{year}-{month:02d}.xlsx"
            )
        },
    )


@router.get("/{daily_id}", response_model=AttendanceDetailResponse)
def attendance_detail(
    daily_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = AttendanceRepository.get_daily_detail(db, daily_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
    daily, employee, shift = row
    return AttendanceDetailResponse(
        daily=_daily_response(daily, employee, shift),
        events=AttendanceRepository.get_events_for_daily(db, daily, shift),
    )


@router.patch("/{daily_id}", response_model=AttendanceDailyResponse)
def adjust_attendance(
    daily_id: int,
    payload: AttendanceAdjustmentRequest,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        result = AttendanceAdjustmentService.adjust(db, daily_id, admin.id, payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
    daily, employee, shift, adjustment = result
    return _daily_response(daily, employee, shift)


@router.get(
    "/{daily_id}/adjustments",
    response_model=list[AttendanceAdjustmentResponse],
)
def attendance_adjustments(
    daily_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if AttendanceRepository.get_daily_detail(db, daily_id) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi chấm công")
    return [
        AttendanceAdjustmentResponse(
            id=adjustment.id,
            attendance_daily_id=adjustment.attendance_daily_id,
            admin_user_id=adjustment.admin_user_id,
            admin_username=username,
            reason=adjustment.reason,
            before_data=adjustment.before_data,
            after_data=adjustment.after_data,
            created_at=adjustment.created_at,
        )
        for adjustment, username in AttendanceRepository.list_adjustments(db, daily_id)
    ]
