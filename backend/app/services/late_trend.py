import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from backend.app.core.config import settings
from backend.app.repositories.attendance_repository import AttendanceRepository


def _shift_month(year, month, offset):
    index = year * 12 + (month - 1) + offset
    return index // 12, index % 12 + 1


def _same_day_last_month(today):
    year, month = _shift_month(today.year, today.month, -1)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(today.day, last_day))


class LateTrendService:
    @staticmethod
    def build(db, days=30, months=6, today=None):
        """Late minutes per day (last `days` days) and per month (last `months` months).

        The month-over-month comparison uses the same number of days in both
        months, so a half-finished current month is not compared against a
        complete previous month.
        """
        today = today or datetime.now(ZoneInfo(settings.TIMEZONE)).date()
        first_month = _shift_month(today.year, today.month, -(months - 1))
        month_start = date(first_month[0], first_month[1], 1)
        daily_start = today - timedelta(days=days - 1)
        # The comparison needs day 1 of last month even when months == 1.
        previous_start = _same_day_last_month(today).replace(day=1)
        query_start = min(month_start, daily_start, previous_start)

        totals = AttendanceRepository.late_totals_by_date(db, query_start, today)

        daily = []
        for offset in range(days):
            work_date = daily_start + timedelta(days=offset)
            minutes, count = totals.get(work_date, (0, 0))
            daily.append(
                {"work_date": work_date, "late_minutes": minutes, "late_count": count}
            )

        buckets = {}
        for offset in range(months):
            buckets[_shift_month(month_start.year, month_start.month, offset)] = [0, 0]
        for work_date, (minutes, count) in totals.items():
            bucket = buckets.get((work_date.year, work_date.month))
            if bucket is not None:
                bucket[0] += minutes
                bucket[1] += count
        monthly = [
            {"year": year, "month": month, "late_minutes": minutes, "late_count": count}
            for (year, month), (minutes, count) in buckets.items()
        ]

        previous_end = _same_day_last_month(today)
        current = sum(
            minutes
            for work_date, (minutes, _) in totals.items()
            if today.replace(day=1) <= work_date <= today
        )
        previous = sum(
            minutes
            for work_date, (minutes, _) in totals.items()
            if previous_start <= work_date <= previous_end
        )
        change = (
            round((current - previous) / previous * 100, 1) if previous else None
        )

        return {
            "daily": daily,
            "monthly": monthly,
            "comparison": {
                "current_minutes": current,
                "previous_minutes": previous,
                "change_percent": change,
                "days": today.day,
            },
        }
