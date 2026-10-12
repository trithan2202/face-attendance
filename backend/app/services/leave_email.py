import html
import logging
import smtplib
import ssl
from datetime import timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.app.core.config import settings
from backend.app.core.logging import log_extra
from backend.app.services.leave_service import SUNDAY, leave_dates, utc_now


logger = logging.getLogger("face_attendance.leave_email")

LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "logo_ACACY.png"

LEAVE_TYPE_LABELS = {
    "ANNUAL": "Nghỉ phép năm",
    "SICK": "Nghỉ ốm",
    "UNPAID": "Nghỉ không lương",
    "OTHER": "Nghỉ khác",
}


def _date(value):
    return value.strftime("%d/%m/%Y")


def _local(value):
    """decided_at được lưu theo UTC không kèm múi giờ; email hiển thị giờ công ty."""
    return (
        value.replace(tzinfo=timezone.utc)
        .astimezone(ZoneInfo(settings.TIMEZONE))
        .strftime("%H:%M %d/%m/%Y")
    )


def _return_date(leave):
    day = leave.end_date + timedelta(days=1)
    while day.weekday() == SUNDAY:
        day += timedelta(days=1)
    return day


def _friendly_error(exc):
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "Máy chủ email từ chối đăng nhập: sai tài khoản hoặc mật khẩu SMTP"
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return "Địa chỉ email của nhân viên bị máy chủ từ chối"
    if isinstance(exc, (TimeoutError, OSError)) and not isinstance(exc, smtplib.SMTPException):
        return f"Không kết nối được máy chủ email ({type(exc).__name__})"
    return f"{type(exc).__name__}: {exc}"[:500]


def build_approval_message(leave, employee, approver, skipped_days=0):
    """Email thông báo đơn nghỉ phép đã được phê duyệt (bản text và HTML)."""
    total_days = len(list(leave_dates(leave)))
    leave_type = LEAVE_TYPE_LABELS.get(leave.leave_type, leave.leave_type)
    department = employee.department.name if employee.department else "—"
    return_date = _return_date(leave)
    start_time = (
        employee.shift.start_time.strftime("%H:%M") if employee.shift else None
    )
    return_text = _date(return_date) + (f", lúc {start_time}" if start_time else "")
    period = f"{_date(leave.start_date)} - {_date(leave.end_date)}"
    contact = " | ".join(
        item for item in (settings.HR_CONTACT_EMAIL, settings.HR_CONTACT_PHONE) if item
    )
    closing = (
        "Chúc Anh/Chị sớm hồi phục sức khỏe."
        if leave.leave_type == "SICK"
        else "Chúc Anh/Chị có khoảng thời gian nghỉ ngơi vui vẻ."
    )

    details = [
        ("Mã nhân viên", employee.employee_code),
        ("Họ và tên", employee.full_name),
        ("Phòng ban", department),
        ("Loại nghỉ", leave_type),
        ("Thời gian nghỉ", f"Từ {_date(leave.start_date)} đến {_date(leave.end_date)}"),
        ("Số ngày nghỉ", f"{total_days} ngày (không tính Chủ nhật)"),
        ("Lý do", leave.reason),
        ("Người phê duyệt", approver),
        ("Thời gian phê duyệt", _local(leave.decided_at)),
    ]
    if leave.decision_note:
        details.append(("Ghi chú phê duyệt", leave.decision_note))

    reminders = [
        "Hoàn tất bàn giao công việc đang phụ trách cho người được phân công trước khi nghỉ.",
        "Thông báo lịch nghỉ cho quản lý trực tiếp và các đồng nghiệp liên quan.",
        "Giữ liên lạc khi có việc khẩn cấp cần trao đổi trong thời gian nghỉ.",
        f"Có mặt làm việc trở lại vào ngày {return_text}.",
        "Trường hợp cần thay đổi hoặc hủy lịch nghỉ, vui lòng báo Phòng Hành chính - "
        "Nhân sự trước ngày bắt đầu nghỉ.",
    ]
    skipped_note = (
        f"Lưu ý: {skipped_days} ngày trong khoảng nghỉ đã có dữ liệu chấm công thực tế "
        "nên hệ thống giữ nguyên công của những ngày này."
        if skipped_days
        else None
    )

    message = EmailMessage()
    message["Subject"] = (
        f"[{settings.COMPANY_NAME}] Thông báo phê duyệt đơn nghỉ phép - "
        f"{employee.full_name} ({period})"
    )
    message["From"] = formataddr((settings.MAIL_FROM_NAME, settings.MAIL_FROM))
    message["To"] = formataddr((employee.full_name, employee.email))
    if settings.HR_CONTACT_EMAIL and settings.HR_CONTACT_EMAIL != settings.MAIL_FROM:
        message["Reply-To"] = settings.HR_CONTACT_EMAIL

    text_lines = [
        f"Kính gửi Anh/Chị {employee.full_name},",
        "",
        "Phòng Hành chính - Nhân sự trân trọng thông báo: đơn xin nghỉ phép của "
        "Anh/Chị đã được PHÊ DUYỆT. Thông tin chi tiết như sau:",
        "",
        *[f"- {label}: {value}" for label, value in details],
        "",
        *([skipped_note, ""] if skipped_note else []),
        "Thời gian nghỉ đã được cập nhật vào hệ thống chấm công. Anh/Chị vui lòng:",
        *[f"  {index}. {item}" for index, item in enumerate(reminders, start=1)],
        "",
        *([f"Mọi thắc mắc xin liên hệ: {contact}", ""] if contact else []),
        closing,
        "",
        "Trân trọng,",
        "Phòng Hành chính - Nhân sự",
        settings.COMPANY_NAME,
        "",
        "---",
        "Đây là email tự động từ Hệ thống chấm công. Vui lòng không trả lời trực tiếp email này.",
    ]
    message.set_content("\n".join(text_lines))

    e = html.escape
    logo_cid = make_msgid(domain="face-attendance.local")
    rows = "".join(
        f'<tr><td style="padding:8px 12px;border:1px solid #e2e8f0;background:#f8fafc;'
        f'width:38%;color:#475569">{e(label)}</td>'
        f'<td style="padding:8px 12px;border:1px solid #e2e8f0;color:#0f172a">'
        f"{e(str(value))}</td></tr>"
        for label, value in details
    )
    reminder_items = "".join(
        f'<li style="margin:0 0 6px">{e(item)}</li>' for item in reminders
    )
    skipped_html = (
        f'<p style="margin:16px 0;padding:10px 12px;background:#fffbeb;'
        f'border-left:4px solid #f59e0b;color:#92400e">{e(skipped_note)}</p>'
        if skipped_note
        else ""
    )
    contact_html = (
        f'<p style="margin:16px 0 0">Mọi thắc mắc xin liên hệ: <strong>{e(contact)}</strong></p>'
        if contact
        else ""
    )
    logo_html = (
        f'<img src="cid:{logo_cid[1:-1]}" alt="{e(settings.COMPANY_NAME)}" height="48" '
        f'style="display:block;height:48px">'
        if LOGO_PATH.exists()
        else f'<strong style="font-size:20px;color:#ffffff">{e(settings.COMPANY_NAME)}</strong>'
    )
    message.add_alternative(
        f"""<!doctype html>
<html lang="vi"><body style="margin:0;padding:24px;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#1e293b">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e2e8f0">
<tr><td style="background:#3a5fae;padding:16px 24px">{logo_html}</td></tr>
<tr><td style="padding:24px">
<p style="margin:0 0 4px;font-size:18px;font-weight:bold;color:#0f172a">Thông báo phê duyệt đơn nghỉ phép</p>
<p style="margin:0 0 20px"><span style="display:inline-block;padding:2px 10px;border-radius:12px;background:#d1fae5;color:#047857;font-weight:bold;font-size:13px">&#10003; Đã phê duyệt</span></p>
<p style="margin:0 0 12px">Kính gửi Anh/Chị <strong>{e(employee.full_name)}</strong>,</p>
<p style="margin:0 0 16px">Phòng Hành chính - Nhân sự trân trọng thông báo: đơn xin nghỉ phép của Anh/Chị đã được <strong style="color:#047857">phê duyệt</strong>. Thông tin chi tiết như sau:</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px">{rows}</table>
{skipped_html}
<p style="margin:20px 0 8px">Thời gian nghỉ đã được cập nhật vào hệ thống chấm công. Anh/Chị vui lòng:</p>
<ol style="margin:0;padding-left:20px">{reminder_items}</ol>
{contact_html}
<p style="margin:16px 0 0">{e(closing)}</p>
<p style="margin:20px 0 0">Trân trọng,<br><strong>Phòng Hành chính - Nhân sự</strong><br>{e(settings.COMPANY_NAME)}</p>
</td></tr>
<tr><td style="padding:12px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b">Đây là email tự động từ Hệ thống chấm công. Vui lòng không trả lời trực tiếp email này.</td></tr>
</table></body></html>""",
        subtype="html",
    )
    if LOGO_PATH.exists():
        message.get_payload()[1].add_related(
            LOGO_PATH.read_bytes(), maintype="image", subtype="png", cid=logo_cid
        )
    return message


def smtp_send(message):
    context = ssl.create_default_context()
    if settings.SMTP_USE_SSL:
        client = smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS, context=context,
        )
    else:
        client = smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        )
    with client:
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            client.starttls(context=context)
        if settings.SMTP_USERNAME:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        client.send_message(message)


class LeaveEmailService:
    # Tests replace this with a fake to avoid touching the network.
    sender = staticmethod(smtp_send)

    @classmethod
    def notify_approved(cls, db, leave, employee, approver, skipped_days=0):
        """Gửi email báo duyệt và lưu kết quả vào đơn. Không bao giờ ném lỗi:
        đơn đã được duyệt dù email có gửi được hay không."""
        if not employee.email:
            status, error = "NO_EMAIL", "Nhân viên chưa có địa chỉ email"
        elif not settings.SMTP_HOST or not settings.MAIL_FROM:
            status, error = "NOT_CONFIGURED", "Chưa cấu hình máy chủ gửi email (SMTP)"
        else:
            try:
                cls.sender(build_approval_message(leave, employee, approver, skipped_days))
                status, error = "SENT", None
            except Exception as exc:  # noqa: BLE001 - mọi lỗi gửi đều ghi nhận vào đơn
                status, error = "FAILED", _friendly_error(exc)

        leave.email_status = status
        leave.email_error = error
        leave.email_sent_at = utc_now() if status == "SENT" else None
        db.commit()

        log = logger.info if status == "SENT" else logger.warning
        log(
            "Leave approval email processed",
            extra=log_extra(
                "leave_email_processed",
                leave_id=leave.id,
                employee_code=employee.employee_code,
                email_status=status,
                error=error,
            ),
        )
        return status
