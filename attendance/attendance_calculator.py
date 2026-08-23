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

    @staticmethod
    def format_duration(minutes):
        """Đổi số phút sang chuỗi hh:mm để hiển thị trên báo cáo."""
        minutes = max(0, int(minutes or 0))

        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    @classmethod
    def calculate_checkout(
        cls,
        check_in,
        check_out,
        work_date,
        shift,
        overtime_min_minutes=0
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

        # Tăng ca luôn neo vào giờ kết thúc của CA LÀM, không phụ thuộc giờ
        # check-in. Ca hành chính kết thúc 18:00 thì phút tăng ca đầu tiên là
        # 18:01, dù hôm đó nhân viên vào muộn hay vào sớm.
        overtime_minutes = 0

        if check_out > shift_end:
            overtime_minutes = int(
                (
                    check_out - shift_end
                ).total_seconds()
                // 60
            )

        # Dưới ngưỡng tối thiểu thì coi như tan ca bình thường, không tạo bản
        # ghi tăng ca phải duyệt chỉ vì ra trễ vài phút.
        if overtime_minutes < overtime_min_minutes:
            overtime_minutes = 0

        is_overtime = overtime_minutes > 0

        return {
            "worked_minutes": worked_minutes,
            "is_early_leave": is_early,
            "early_leave_minutes": early_minutes,
            "is_overtime": is_overtime,
            "overtime_minutes": overtime_minutes
        }

    @classmethod
    def recalculate(cls, daily, shift, overtime_min_minutes=0):
        """Recompute every derived column of a daily row from its timestamps.

        Shared by the kiosk attendance flow and the manual adjustment service so
        both always land on the same status and metrics.
        """
        daily.worked_minutes = 0
        daily.late_minutes = 0
        daily.early_leave_minutes = 0
        daily.overtime_minutes = 0
        daily.is_late = False
        daily.is_early_leave = False
        daily.is_overtime = False

        if daily.first_check_in is None:
            # A leave that was approved for this day survives as long as nobody
            # actually scanned in.
            if daily.status != "ON_LEAVE":
                daily.status = (
                    "MISSING_CHECK_IN" if daily.last_check_out else "ABSENT"
                )
            daily.overtime_status = "NONE"
            return

        daily.is_late, daily.late_minutes = cls.calculate_late(
            daily.first_check_in, daily.work_date, shift
        )
        if daily.last_check_out is None:
            daily.status = "MISSING_CHECK_OUT"
            daily.overtime_status = "NONE"
            return

        metrics = cls.calculate_checkout(
            daily.first_check_in,
            daily.last_check_out,
            daily.work_date,
            shift,
            overtime_min_minutes,
        )
        for field, value in metrics.items():
            setattr(daily, field, value)
        daily.status = "PRESENT"
        # Changing the times invalidates any previous decision: overtime has to
        # be approved again.
        daily.overtime_status = "PENDING" if daily.is_overtime else "NONE"