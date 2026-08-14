# Database và API

## Database

Giữ các bảng hiện có: `employees`, `shifts`, `face_embeddings`, `attendance_events`, `attendance_daily`. Chuyển tạo schema sang Alembic migration.

Thêm các bảng:

- `admin_users`: tài khoản quản trị local, password hash, trạng thái và timestamps.
- `attendance_adjustments`: bản ghi audit cho mọi chỉnh sửa công: attendance daily, admin, lý do, dữ liệu trước/sau, thời điểm.

`face_embeddings` chỉ lưu vector float32 đã mã hóa. Không thêm đường dẫn ảnh, blob ảnh hay dữ liệu video.

## Quy tắc dữ liệu

- Một `attendance_daily` duy nhất cho mỗi nhân viên và work date.
- Đăng ký khuôn mặt xóa toàn bộ embedding cũ và thay bằng 10 sample + 1 centroid trong cùng transaction.
- Nhân viên chỉ `ACTIVE` sau khi enrollment thành công; hủy enrollment không để lại nhân viên hoặc embedding mồ côi.
- Điều chỉnh công cập nhật daily record, ghi audit bắt buộc và tính lại các chỉ số liên quan.

## Nhóm API

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
- `GET /api/health`, `GET /api/worker/status`.
- `/api/admin/employees`: danh sách, tạo, sửa, ngưng hoạt động, enrollment status và đăng ký lại.
- `/api/admin/shifts`: CRUD ca.
- `/api/admin/attendance`: danh sách có lọc, chi tiết events, điều chỉnh, audit, export Excel theo ngày và báo cáo công theo tháng.
- `/api/kiosk`: lấy trạng thái camera, bắt đầu/hủy phiên liveness và nhận kết quả nhận diện.

Tất cả `/api/admin/*` yêu cầu JWT quản trị; health và kiosk không yêu cầu đăng nhập. Response lỗi dùng định dạng nhất quán gồm mã, thông điệp tiếng Việt và chi tiết an toàn.
