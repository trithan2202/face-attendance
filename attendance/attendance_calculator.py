from datetime import datetime, timedelta


class AttendanceCalculator:
    @staticmethod
    def shift_start(work_date, shift):
        return datetime.combine(
            work_date,
            shift.start_time
        )

    @staticmethod
    def shift_end(work_date, shift):
        end = datetime.combine(
            work_date,
            shift.end_time
        )

        if shift.cross_day:
            end += timedelta(days=1)

        return end

    @classmethod
    def calculate_late(
        cls,
        check_in,
        work_date,
        shift
    ):
        allowed_time = (
            cls.shift_start(
                work_date,
                shift
            )
            + timedelta(
                minutes=shift.late_grace_minutes
            )
        )

        if check_in <= allowed_time:
            return False, 0

        minutes = int(
            (
                check_in - allowed_time
            ).total_seconds()
            // 60
        )

        return True, minutes

    @classmethod
    def calculate_checkout(
        cls,
        check_in,
        check_out,
        work_date,
        shift
    ):
        worked_minutes = max(
            0,
            int(
                (
                    check_out - check_in
                ).total_seconds()
                // 60
            )
        )

        shift_end = cls.shift_end(
            work_date,
            shift
        )

        early_limit = (
            shift_end
            - timedelta(
                minutes=(
                    shift.early_leave_grace_minutes
                )
            )
        )

        is_early = check_out < early_limit

        early_minutes = 0

        if is_early:
            early_minutes = int(
                (
                    early_limit - check_out
                ).total_seconds()
                // 60
            )

        is_overtime = check_out > shift_end

        overtime_minutes = 0

        if is_overtime:
            overtime_minutes = int(
                (
                    check_out - shift_end
                ).total_seconds()
                // 60
            )

        return {
            "worked_minutes": worked_minutes,
            "is_early_leave": is_early,
            "early_leave_minutes": early_minutes,
            "is_overtime": is_overtime,
            "overtime_minutes": overtime_minutes
        }