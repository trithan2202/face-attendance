import calendar
import io
from datetime import date, datetime, timedelta

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from attendance.attendance_calculator import AttendanceCalculator
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.services.settings_service import SettingsService


XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

THIN_BLACK = Side(style="thin", color="000000")
GRID_BORDER = Border(
    left=THIN_BLACK,
    right=THIN_BLACK,
    top=THIN_BLACK,
    bottom=THIN_BLACK,
)
HEADER_FILL = PatternFill("solid", fgColor="A6A6A6")
SUBHEADER_FILL = PatternFill("solid", fgColor="B7B7B7")
WORKDAY_FILL = PatternFill("solid", fgColor="FFF200")
PRESENT_FILL = PatternFill("solid", fgColor="57D16C")
WARNING_FILL = PatternFill("solid", fgColor="F8CBAD")
ABSENT_FILL = PatternFill("solid", fgColor="F4CCCC")
LEAVE_FILL = PatternFill("solid", fgColor="BDD7EE")
WEEKEND_FILL = PatternFill("solid", fgColor="FF4D4D")
INVALID_DAY_FILL = PatternFill("solid", fgColor="D9D9D9")
OT_INFO_FILL = PatternFill("solid", fgColor="5B9BD5")
OT_DATE_GROUP_FILL = PatternFill("solid", fgColor="FFC000")
OT_DATE_FILL = PatternFill("solid", fgColor="FF0000")
OT_TOTAL_FILL = PatternFill("solid", fgColor="82DC8C")
OT_NOTE_FILL = PatternFill("solid", fgColor="F2F2F2")


def _safe_text(value):
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def _department_name(employee):
    return _safe_text(
        employee.department.name if employee.department else None
    )


def _shift_minutes(shift):
    if shift is None:
        return 0
    start = datetime.combine(date.min, shift.start_time)
    end = datetime.combine(date.min, shift.end_time)
    if shift.cross_day or end <= start:
        end += timedelta(days=1)
    return max(0, int((end - start).total_seconds() // 60))


def _workday_code(daily, shift, half_day_ratio=0.75):
    if daily is None:
        return "", None
    if daily.status == "ABSENT":
        return "V", 0
    if daily.status == "MISSING_CHECK_IN":
        return "TCI", 0
    if daily.status == "MISSING_CHECK_OUT":
        return "TCO", 0
    if daily.status == "ON_LEAVE":
        return "NP", 0
    if daily.status != "PRESENT":
        return _safe_text(daily.status), 0

    scheduled_minutes = _shift_minutes(shift)
    if scheduled_minutes and daily.worked_minutes < scheduled_minutes * half_day_ratio:
        return "0.5HC", 0.5
    return "HC", 1


def _status_label(status):
    return {
        "PRESENT": "Có mặt",
        "MISSING_CHECK_IN": "Thiếu check-in",
        "MISSING_CHECK_OUT": "Thiếu check-out",
        "ABSENT": "Vắng",
        "ON_LEAVE": "Nghỉ phép",
    }.get(status, status)


def _overtime_hours(minutes):
    """Quy giờ tăng ca về số giờ tròn.

    Phần lẻ dưới 30 phút thì làm tròn xuống, từ 30 phút trở lên làm tròn lên:
    1:15 thành 1 giờ, 1:45 thành 2 giờ.
    """
    return (max(0, int(minutes or 0)) + 30) // 60


def _overtime_status_label(status):
    return {
        "NONE": "",
        "PENDING": "Chờ duyệt",
        "APPROVED": "Đã duyệt",
        "REJECTED": "Từ chối",
    }.get(status, status)


MONTH_ABBR = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)

# Ba dòng tiêu đề nằm trên cùng của hai sheet báo cáo tháng: tên bảng, kỳ báo
# cáo và ngày xuất. Bảng dữ liệu vì vậy bắt đầu từ dòng thứ tư.
REPORT_HEADER_ROWS = 3


def _add_report_header(sheet, year, month):
    """Tiêu đề "BẢNG CHẤM CÔNG AUG.26" cùng kỳ báo cáo và ngày xuất."""
    last_day = calendar.monthrange(year, month)[1]

    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
    title = sheet.cell(
        row=1,
        column=1,
        value=f"BẢNG CHẤM CÔNG {MONTH_ABBR[month - 1]}.{year % 100:02d}",
    )
    title.font = Font(name="Times New Roman", bold=True, size=14)
    title.alignment = Alignment(horizontal="left", vertical="center")

    # Nhãn nằm ở A:B đã gộp, ngày nằm ở cột C và E - đây là những cột đủ rộng
    # trên cả hai sheet; cột ngày công chỉ rộng hơn 4 nên đặt ngày vào đó sẽ
    # hiện thành "#####".
    info_rows = (
        (2, "Từ ngày:", date(year, month, 1), "Đến ngày:", date(year, month, last_day)),
        (3, "Ngày xuất BC:", date.today(), None, None),
    )
    for row, label, value, second_label, second_value in info_rows:
        sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        for column, content in (
            (1, label), (3, value), (4, second_label), (5, second_value)
        ):
            if content is None:
                continue
            cell = sheet.cell(row=row, column=column, value=content)
            cell.font = Font(
                name="Times New Roman", size=11, bold=column in {1, 4}
            )
            cell.alignment = Alignment(horizontal="left", vertical="center")
            if isinstance(content, date):
                cell.number_format = "dd/mm/yyyy"

    sheet.row_dimensions[1].height = 22
    sheet.row_dimensions[2].height = 18
    sheet.row_dimensions[3].height = 18


def _new_workbook(title):
    workbook = Workbook()
    workbook.remove(workbook.active)
    workbook.properties.title = title
    workbook.properties.creator = "Face Attendance"
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"
    return workbook


def _save(workbook):
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def build_daily_workbook(rows, date_from=None, date_to=None):
    workbook = _new_workbook("Báo cáo chấm công")
    sheet = workbook.create_sheet("Cham cong")
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A5"

    title = "BÁO CÁO CHẤM CÔNG"
    if date_from and date_to and date_from == date_to:
        title += f" NGÀY {date_from.strftime('%d/%m/%Y')}"
    elif date_from:
        title += f" TỪ {date_from.strftime('%d/%m/%Y')}"
    elif date_to:
        title += f" ĐẾN {date_to.strftime('%d/%m/%Y')}"
    sheet.merge_cells("A1:M2")
    title_cell = sheet["A1"]
    title_cell.value = title
    title_cell.font = Font(name="Arial", size=16, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor="1F4E78")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[1].height = 24
    sheet.row_dimensions[2].height = 12

    sheet["A3"] = "Thời điểm xuất:"
    sheet["B3"] = datetime.now()
    sheet["B3"].number_format = "dd/mm/yyyy hh:mm"
    sheet["A3"].font = Font(name="Arial", italic=True, color="666666")
    sheet["B3"].font = Font(name="Arial", italic=True, color="666666")

    headers = [
        "Mã nhân viên",
        "Họ tên",
        "Phòng ban",
        "Ca",
        "Ngày công",
        "Check-in",
        "Check-out",
        "Phút làm",
        "Đi trễ",
        "Về sớm",
        "Tăng ca",
        "Trạng thái",
        "Duyệt OT",
    ]
    for column, value in enumerate(headers, start=1):
        cell = sheet.cell(row=4, column=column, value=value)
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = GRID_BORDER
    sheet.row_dimensions[4].height = 30

    for row_index, (daily, employee, shift) in enumerate(rows, start=5):
        values = [
            _safe_text(employee.employee_code),
            _safe_text(employee.full_name),
            _department_name(employee),
            _safe_text(shift.code),
            daily.work_date,
            daily.first_check_in,
            daily.last_check_out,
            daily.worked_minutes,
            daily.late_minutes,
            daily.early_leave_minutes,
            AttendanceCalculator.format_duration(daily.overtime_minutes),
            _status_label(daily.status),
            _overtime_status_label(daily.overtime_status),
        ]
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row_index, column=column, value=value)
            cell.font = Font(name="Arial", size=10)
            cell.border = GRID_BORDER
            cell.alignment = Alignment(
                horizontal="left" if column in {1, 2, 3, 4, 12} else "center",
                vertical="center",
            )
        sheet.cell(row=row_index, column=5).number_format = "dd/mm/yyyy"
        sheet.cell(row=row_index, column=6).number_format = "dd/mm/yyyy hh:mm"
        sheet.cell(row=row_index, column=7).number_format = "dd/mm/yyyy hh:mm"
        if row_index % 2 == 0:
            for column in range(1, 14):
                sheet.cell(row=row_index, column=column).fill = PatternFill(
                    "solid", fgColor="EAF2F8"
                )

    last_row = max(4, 4 + len(rows))
    sheet.auto_filter.ref = f"A4:M{last_row}"
    widths = [16, 28, 20, 12, 14, 20, 20, 12, 11, 11, 11, 20, 14]
    for column, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = "1:4"
    return _save(workbook)


def build_monthly_workbook(
    employees,
    attendance_rows,
    year,
    month,
    half_day_ratio=0.75,
):
    workbook = _new_workbook(f"Báo cáo công tháng {month}/{year}")
    sheet = workbook.create_sheet(f"Thang {month:02d}-{year}")
    sheet.sheet_view.showGridLines = False
    _add_report_header(sheet, year, month)

    # Bảng nằm dưới khối tiêu đề: hai dòng tiêu đề cột rồi mới tới nhân viên.
    top = REPORT_HEADER_ROWS
    head_row, day_row, first_data_row = top + 1, top + 2, top + 3
    sheet.freeze_panes = f"F{first_data_row}"

    last_day = calendar.monthrange(year, month)[1]
    employee_rows = list(employees)
    attendance = {
        (daily.employee_id, daily.work_date.day): (daily, shift)
        for daily, _employee, shift in attendance_rows
    }

    headers = ["STT", "MÃ NHÂN VIÊN", "TÊN NHÂN VIÊN", "PHÒNG BAN", "CA LÀM"]
    for column, value in enumerate(headers, start=1):
        sheet.merge_cells(
            start_row=head_row, start_column=column,
            end_row=day_row, end_column=column,
        )
        cell = sheet.cell(row=head_row, column=column, value=value)
        cell.fill = HEADER_FILL
        cell.font = Font(name="Times New Roman", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = GRID_BORDER

    sheet.merge_cells(
        start_row=head_row, start_column=6, end_row=head_row, end_column=36
    )
    month_cell = sheet.cell(row=head_row, column=6, value=f"THÁNG {month}/{year}")
    month_cell.fill = HEADER_FILL
    month_cell.font = Font(name="Times New Roman", bold=True, size=11)
    month_cell.alignment = Alignment(horizontal="center", vertical="center")
    month_cell.border = GRID_BORDER

    sheet.merge_cells(
        start_row=head_row, start_column=37, end_row=day_row, end_column=37
    )
    total_header = sheet.cell(row=head_row, column=37, value="TỔNG NGÀY\nCÔNG")
    total_header.fill = HEADER_FILL
    total_header.font = Font(name="Times New Roman", bold=True, size=10)
    total_header.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    total_header.border = GRID_BORDER

    for day in range(1, 32):
        column = day + 5
        cell = sheet.cell(row=day_row, column=column, value=day)
        valid_day = day <= last_day
        is_sunday = valid_day and date(year, month, day).weekday() == 6
        cell.fill = (
            WEEKEND_FILL if is_sunday else SUBHEADER_FILL if valid_day else INVALID_DAY_FILL
        )
        cell.font = Font(
            name="Times New Roman",
            bold=True,
            size=9,
            color="FFFFFF" if is_sunday else "000000",
        )
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = GRID_BORDER

    for row_index, (employee, shift) in enumerate(employee_rows, start=first_data_row):
        info_values = [
            row_index - first_data_row + 1,
            _safe_text(employee.employee_code),
            _safe_text(employee.full_name),
            _department_name(employee),
            _safe_text(shift.code if shift else ""),
        ]
        for column, value in enumerate(info_values, start=1):
            cell = sheet.cell(row=row_index, column=column, value=value)
            cell.font = Font(
                name="Times New Roman",
                size=10,
                bold=column == 1,
            )
            cell.alignment = Alignment(
                horizontal="center" if column in {1, 5} else "left",
                vertical="center",
            )
            cell.border = GRID_BORDER

        for day in range(1, 32):
            column = day + 5
            cell = sheet.cell(row=row_index, column=column)
            cell.border = GRID_BORDER
            cell.font = Font(name="Times New Roman", size=9)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if day > last_day:
                cell.fill = INVALID_DAY_FILL
                continue
            cell.fill = WORKDAY_FILL
            item = attendance.get((employee.id, day))
            if item is None:
                continue
            daily, daily_shift = item
            code, _value = _workday_code(daily, daily_shift, half_day_ratio)
            cell.value = code
            if code in {"HC", "0.5HC"}:
                cell.fill = PRESENT_FILL
            elif code in {"TCO", "TCI"}:
                cell.fill = WARNING_FILL
            elif code == "V":
                cell.fill = ABSENT_FILL
            elif code == "NP":
                cell.fill = LEAVE_FILL

        total_cell = sheet.cell(row=row_index, column=37)
        total_cell.value = (
            f'=COUNTIF(F{row_index}:AJ{row_index},"HC")+'
            f'0.5*COUNTIF(F{row_index}:AJ{row_index},"0.5HC")'
        )
        total_cell.number_format = "0.0#"
        total_cell.font = Font(name="Times New Roman", bold=True, size=10)
        total_cell.alignment = Alignment(horizontal="center", vertical="center")
        total_cell.border = GRID_BORDER
        sheet.row_dimensions[row_index].height = 22

    sheet.row_dimensions[head_row].height = 25
    sheet.row_dimensions[day_row].height = 22
    widths = {1: 6, 2: 16, 3: 28, 4: 18, 5: 13, 37: 13}
    for column, width in widths.items():
        sheet.column_dimensions[get_column_letter(column)].width = width
    for column in range(6, 37):
        sheet.column_dimensions[get_column_letter(column)].width = 4.3

    legend_row = max(5, len(employee_rows) + 5) + top
    sheet.merge_cells(start_row=legend_row, start_column=1, end_row=legend_row, end_column=12)
    legend = sheet.cell(
        row=legend_row,
        column=1,
        value=(
            "Quy ước: HC = đủ công; 0.5HC = nửa công; TCO = thiếu check-out; "
            "TCI = thiếu check-in; V = vắng; NP = nghỉ phép"
        ),
    )
    legend.font = Font(name="Times New Roman", italic=True, size=10)
    legend.alignment = Alignment(horizontal="left", vertical="center")

    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = f"1:{day_row}"
    sheet.print_area = f"A1:AK{max(legend_row, len(employee_rows) + day_row)}"
    _add_overtime_sheet(workbook, attendance_rows, year, month)
    return _save(workbook)


def _add_overtime_sheet(workbook, attendance_rows, year, month):
    sheet = workbook.create_sheet("Công OT")
    sheet.sheet_view.showGridLines = False
    _add_report_header(sheet, year, month)

    top = REPORT_HEADER_ROWS
    head_row, day_row, first_data_row = top + 1, top + 2, top + 3
    sheet.freeze_panes = f"E{first_data_row}"

    # Only overtime an admin has signed off on is billable, so the sheet is the
    # approved set rather than everything the clock produced.
    overtime_rows = [
        (daily, employee, shift)
        for daily, employee, shift in attendance_rows
        if daily.overtime_minutes > 0 and daily.overtime_status == "APPROVED"
    ]
    overtime_dates = sorted({daily.work_date for daily, _employee, _shift in overtime_rows})
    employee_data = {}
    overtime_hours = {}
    for daily, employee, _shift in overtime_rows:
        employee_data.setdefault(employee.id, employee)
        # Bảng OT chỉ tính theo giờ tròn nên lưu thẳng số giờ đã làm tròn, ô
        # vừa hiện đúng con số vừa cộng được bằng SUM.
        overtime_hours[(employee.id, daily.work_date)] = _overtime_hours(
            daily.overtime_minutes
        )
    employees = sorted(
        employee_data.values(),
        key=lambda employee: employee.employee_code,
    )

    day_count = max(1, len(overtime_dates))
    first_day_column = 5
    last_day_column = first_day_column + day_count - 1
    total_column = last_day_column + 1
    note_column = total_column + 1

    static_headers = ["STT", "Mã NV", "TÊN NHÂN VIÊN", "PHÒNG BAN"]
    for column, value in enumerate(static_headers, start=1):
        sheet.merge_cells(
            start_row=head_row,
            start_column=column,
            end_row=day_row,
            end_column=column,
        )
        cell = sheet.cell(row=head_row, column=column, value=value)
        cell.fill = OT_INFO_FILL
        cell.font = Font(name="Times New Roman", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = GRID_BORDER

    if last_day_column > first_day_column:
        sheet.merge_cells(
            start_row=head_row,
            start_column=first_day_column,
            end_row=head_row,
            end_column=last_day_column,
        )
    date_group = sheet.cell(row=head_row, column=first_day_column, value="Ngày (tiếng)")
    date_group.fill = OT_DATE_GROUP_FILL
    date_group.font = Font(name="Times New Roman", bold=True, size=11)
    date_group.alignment = Alignment(horizontal="center", vertical="center")
    date_group.border = GRID_BORDER

    for offset in range(day_count):
        column = first_day_column + offset
        value = overtime_dates[offset] if offset < len(overtime_dates) else "-"
        cell = sheet.cell(row=day_row, column=column, value=value)
        cell.fill = OT_DATE_FILL
        cell.font = Font(name="Times New Roman", bold=True, size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = GRID_BORDER
        if isinstance(value, date):
            cell.number_format = "dd/mm"

    for column, value, fill in (
        (total_column, "Total", OT_TOTAL_FILL),
        (note_column, "Note", OT_NOTE_FILL),
    ):
        sheet.merge_cells(
            start_row=head_row,
            start_column=column,
            end_row=day_row,
            end_column=column,
        )
        cell = sheet.cell(row=head_row, column=column, value=value)
        cell.fill = fill
        cell.font = Font(name="Times New Roman", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = GRID_BORDER

    if employees:
        for row_index, employee in enumerate(employees, start=first_data_row):
            info_values = [
                row_index - first_data_row + 1,
                _safe_text(employee.employee_code),
                _safe_text(employee.full_name),
                _department_name(employee),
            ]
            for column, value in enumerate(info_values, start=1):
                cell = sheet.cell(row=row_index, column=column, value=value)
                cell.font = Font(name="Times New Roman", size=11)
                cell.alignment = Alignment(
                    horizontal="center" if column in {1, 4} else "left",
                    vertical="center",
                )
                cell.border = GRID_BORDER

            for offset, overtime_date in enumerate(overtime_dates):
                column = first_day_column + offset
                cell = sheet.cell(
                    row=row_index,
                    column=column,
                    value=overtime_hours.get((employee.id, overtime_date)),
                )
                cell.number_format = "0"
                cell.font = Font(name="Times New Roman", size=11)
                # Canh giữa cho thẳng cột với tiêu đề ngày phía trên.
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = GRID_BORDER

            first_letter = get_column_letter(first_day_column)
            last_letter = get_column_letter(last_day_column)
            total_cell = sheet.cell(row=row_index, column=total_column)
            total_cell.value = f"=SUM({first_letter}{row_index}:{last_letter}{row_index})"
            total_cell.number_format = "0"
            total_cell.font = Font(name="Times New Roman", bold=True, size=11)
            total_cell.alignment = Alignment(horizontal="center", vertical="center")
            total_cell.border = GRID_BORDER

            note_cell = sheet.cell(row=row_index, column=note_column)
            note_cell.font = Font(name="Times New Roman", size=11)
            note_cell.border = GRID_BORDER
            sheet.row_dimensions[row_index].height = 23
        last_row = len(employees) + day_row
    else:
        last_row = first_data_row
        sheet.merge_cells(
            start_row=first_data_row,
            start_column=1,
            end_row=first_data_row,
            end_column=note_column,
        )
        empty_cell = sheet.cell(
            row=first_data_row, column=1, value="Không có dữ liệu tăng ca trong tháng"
        )
        empty_cell.font = Font(name="Times New Roman", italic=True, size=11, color="666666")
        empty_cell.alignment = Alignment(horizontal="center", vertical="center")
        empty_cell.border = GRID_BORDER
        sheet.row_dimensions[first_data_row].height = 28

    sheet.row_dimensions[head_row].height = 30
    sheet.row_dimensions[day_row].height = 24
    widths = {1: 7, 2: 18, 3: 32, 4: 22, total_column: 14, note_column: 18}
    for column, width in widths.items():
        sheet.column_dimensions[get_column_letter(column)].width = width
    # Cột ngày chỉ cần đủ cho tiêu đề "dd/mm" và số giờ tăng ca bên dưới; để
    # rộng hơn thì bảng bị kéo dài vô ích khi tháng có nhiều ngày OT.
    for column in range(first_day_column, last_day_column + 1):
        sheet.column_dimensions[get_column_letter(column)].width = 8

    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = f"1:{day_row}"
    sheet.print_area = f"A1:{get_column_letter(note_column)}{last_row}"


def build_monthly_report(db, year, month, employee_id=None, department_id=None):
    start_date = date(year, month, 1)
    end_date = date(year, month, calendar.monthrange(year, month)[1])
    employees = AttendanceRepository.list_employees_for_report(
        db,
        employee_id=employee_id,
        department_id=department_id,
        date_from=start_date,
        date_to=end_date,
    )
    rows = AttendanceRepository.list_daily(
        db,
        date_from=start_date,
        date_to=end_date,
        employee_id=employee_id,
        department_id=department_id,
    )
    return build_monthly_workbook(
        employees,
        rows,
        year,
        month,
        half_day_ratio=SettingsService.get_float(db, "HALF_DAY_RATIO"),
    )
