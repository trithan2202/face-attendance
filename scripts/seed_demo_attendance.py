"""Sinh dữ liệu chấm công mẫu để dashboard và báo cáo có số liệu khi demo.

Chỉ điền vào những ngày làm việc (thứ 2 - thứ 7) mà nhân viên đang hoạt động
chưa có bản ghi; dữ liệu thật đã có không bị ghi đè. Các chỉ số đi trễ, về sớm,
tăng ca được tính bằng chính AttendanceCalculator như khi quét ở kiosk. Dữ liệu
sinh theo hạt giống cố định nên chạy lại cho cùng kết quả.

    python -m scripts.seed_demo_attendance              # 6 tháng gần nhất đến hôm qua
    python -m scripts.seed_demo_attendance --months 3
    python -m scripts.seed_demo_attendance --dry-run
"""

import argparse
import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from attendance.attendance_calculator import AttendanceCalculator
from backend.app.core.config import settings
from backend.app.core.database import get_db_session
from backend.app.models import AttendanceDaily, AttendanceEvent, Employee
from backend.app.services.settings_service import SettingsService


# Tỷ lệ đi trễ thay đổi theo tháng để biểu đồ có xu hướng rõ ràng.
LATE_PROBABILITY = {1: 0.20, 2: 0.24, 3: 0.20, 4: 0.18, 5: 0.30, 6: 0.26,
                    7: 0.22, 8: 0.21, 9: 0.17, 10: 0.23, 11: 0.20, 12: 0.25}


def _months_back(day, months):
    index = day.year * 12 + day.month - 1 - (months - 1)
    return date(index // 12, index % 12 + 1, 1)


def _at(work_date, base, minutes, rng):
    return (
        datetime.combine(work_date, base)
        + timedelta(minutes=minutes, seconds=rng.randint(0, 59))
    )


def _build_day(employee, shift, work_date, today, overtime_min):
    rng = random.Random(f"{employee.employee_code}-{work_date.isoformat()}")
    daily = AttendanceDaily(
        employee_id=employee.id,
        shift_id=shift.id,
        work_date=work_date,
        status="ABSENT",
    )
    roll = rng.random()
    if roll < 0.015:
        AttendanceCalculator.recalculate(daily, shift, overtime_min)
        return daily, []

    if rng.random() < LATE_PROBABILITY[work_date.month]:
        # Trễ quá thời gian ân hạn, phần lớn chỉ vài chục phút.
        offset = shift.late_grace_minutes + 1 + min(110, int(rng.expovariate(1 / 14)))
    else:
        offset = rng.randint(-25, shift.late_grace_minutes - 1)
    daily.first_check_in = _at(work_date, shift.start_time, offset, rng)

    if roll >= 0.03:
        kind = rng.random()
        if kind < 0.08:
            out_offset = -rng.randint(15, 90)
        elif kind < 0.20:
            out_offset = rng.randint(overtime_min + 5, 150)
        else:
            out_offset = rng.randint(-5, 25)
        daily.last_check_out = _at(work_date, shift.end_time, out_offset, rng)

    AttendanceCalculator.recalculate(daily, shift, overtime_min)
    # Tăng ca của những ngày đã qua một tuần coi như quản trị đã xử lý.
    if daily.is_overtime and (today - work_date).days > 7:
        decision = rng.random()
        daily.overtime_status = (
            "APPROVED" if decision < 0.75 else "REJECTED" if decision < 0.9 else "PENDING"
        )

    events = [
        AttendanceEvent(
            employee_id=employee.id,
            event_type=event_type,
            recognized_at=moment,
            similarity=round(rng.uniform(0.6, 0.86), 4),
            detection_score=round(rng.uniform(0.74, 0.88), 4),
        )
        for event_type, moment in (
            ("CHECK_IN", daily.first_check_in),
            ("CHECK_OUT", daily.last_check_out),
        )
        if moment is not None
    ]
    return daily, events


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = datetime.now(ZoneInfo(settings.TIMEZONE)).date()
    # Không sinh dữ liệu cho hôm nay để không chặn lượt quét thật ở kiosk.
    end = today - timedelta(days=1)
    start = _months_back(today, args.months)

    db = get_db_session()
    try:
        overtime_min = SettingsService.get_int(db, "OVERTIME_MIN_MINUTES")
        employees = [
            employee
            for employee in db.scalars(
                select(Employee).where(Employee.status == "ACTIVE")
            )
            if employee.shift is not None
        ]
        existing = set(
            db.execute(
                select(AttendanceDaily.employee_id, AttendanceDaily.work_date).where(
                    AttendanceDaily.work_date >= start,
                    AttendanceDaily.work_date <= end,
                )
            ).all()
        )

        created = late = 0
        work_date = start
        while work_date <= end:
            if work_date.weekday() != 6:
                for employee in employees:
                    if (employee.id, work_date) in existing:
                        continue
                    daily, events = _build_day(
                        employee, employee.shift, work_date, today, overtime_min
                    )
                    db.add(daily)
                    db.add_all(events)
                    created += 1
                    late += daily.is_late
            work_date += timedelta(days=1)

        print(
            f"[DEMO] {start:%d/%m/%Y} - {end:%d/%m/%Y}: {len(employees)} nhân viên, "
            f"tạo {created} ngày công ({late} lượt đi trễ), "
            f"bỏ qua {len(existing)} ngày đã có dữ liệu"
        )
        if args.dry_run:
            db.rollback()
            print("[DEMO] --dry-run: không lưu thay đổi")
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
