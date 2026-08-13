# Face Attendance

## Khởi động backend trên Windows

```powershell
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d postgres
.\scripts\migrate.ps1
.\scripts\run_api.ps1
```

Mở một PowerShell khác để chạy worker:

```powershell
.\scripts\run_recognition_worker.ps1
```

Chạy frontend ở PowerShell khác:

```powershell
Set-Location frontend
npm install
Set-Location ..
.\scripts\run_frontend.ps1
```

Vite proxy `/api` tới `http://127.0.0.1:8000`. Bản Docker/Nginx proxy `/api`
tới API chạy trên Windows host tại cổng 8000.

API documentation: `http://127.0.0.1:8000/api/docs`.

Trước khi migrate, phải thay `JWT_SECRET`, `ADMIN_USERNAME` và
`ADMIN_PASSWORD` trong `.env`. `JWT_SECRET` nên là chuỗi ngẫu nhiên dài tối
thiểu 32 byte.

## Chạy toàn bộ bằng Docker

Sửa `.env` trước, đặc biệt `JWT_SECRET` và `ADMIN_PASSWORD` không được giữ giá
trị mặc định. Sau đó:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

Khi thay đổi `requirements.txt` hoặc gặp lỗi module xử lý khuôn mặt, bắt buộc
rebuild image bằng `docker compose build --no-cache backend`; thao tác restart
container đơn thuần không cài lại dependency Python.

Các địa chỉ:

- Frontend: `http://localhost:3000`
- Backend/API docs: `http://localhost:8000/api/docs`
- PostgreSQL: `localhost:5432`

Backend tự chạy Alembic và seed khi container khởi động. Nếu volume chứa schema
5 bảng từ phiên bản cũ, bootstrap sẽ stamp revision `0001` rồi chỉ thêm các
migration mới; không tạo lại hoặc xóa năm bảng cũ.

### Database đã được tạo bằng script cũ

Nếu database hiện có đã chứa năm bảng `employees`, `shifts`,
`face_embeddings`, `attendance_events`, `attendance_daily` nhưng chưa có bảng
`alembic_version`, chạy quy trình tiếp quản một lần:

```powershell
.\scripts\adopt_existing_db.ps1
```

Không chạy script này cho database mới hoặc database đã được Alembic quản lý.

## Endpoint hệ thống và xác thực

- `GET /api/health`
- `GET /api/worker/status`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET|POST /api/admin/shifts`
- `GET|PUT|DELETE /api/admin/shifts/{shift_id}`
- `GET|POST /api/admin/employees`
- `GET|PUT|DELETE /api/admin/employees/{employee_id}`
- `POST /api/admin/employees/{employee_id}/enrollment`
- `GET|DELETE /api/admin/enrollment/{session_id}`
- `POST /api/admin/enrollment/{session_id}/frame`
- `GET /api/admin/attendance`
- `GET|PATCH /api/admin/attendance/{daily_id}`
- `GET /api/admin/attendance/{daily_id}/adjustments`
- `POST /api/kiosk/liveness`
- `GET|DELETE /api/kiosk/liveness/{session_id}`
- `POST /api/kiosk/liveness/{session_id}/frame`
- `POST /api/kiosk/recognition`
- `GET /api/kiosk/recognition/{session_id}`
- `POST /api/kiosk/recognition/{session_id}/frame`

JWT đăng nhập được lưu trong cookie `HttpOnly`, `SameSite=Lax` và không được
trả về trong JSON.

Các endpoint `/api/admin/*` yêu cầu cookie đăng nhập. `DELETE` nhân viên chỉ
chuyển trạng thái sang `INACTIVE`; dữ liệu lịch sử không bị xóa. Nhân viên mới
có trạng thái `PENDING_ENROLLMENT` và chỉ được chuyển sang `ACTIVE` sau khi có
đúng 10 embedding mẫu cùng một centroid.

Frame enrollment được gửi dạng `multipart/form-data` với field `frame`. Backend
chỉ xử lý frame trong bộ nhớ; ảnh không được lưu ra filesystem hoặc database.

Liveness kiosk không yêu cầu đăng nhập. Backend chọn ngẫu nhiên thử thách chớp
mắt, quay trái hoặc quay phải và sử dụng MediaPipe Face Mesh để theo dõi
landmark. Đây là lớp bảo vệ cho demo local, không phải hệ thống chống giả mạo
sinh trắc học cấp cao.

Kết quả liveness chỉ được dùng một lần và phải đổi sang phiên recognition trong
thời gian ngắn. Recognition yêu cầu cùng mã nhân viên xuất hiện tối thiểu 3 lần
trong cửa sổ 5 frame trước khi ghi `CHECK_IN` hoặc `CHECK_OUT`.

Danh sách chấm công hỗ trợ lọc theo khoảng ngày, nhân viên, phòng ban và trạng
thái. Điều chỉnh bắt buộc có lý do; backend lưu snapshot trước/sau cùng tài
khoản admin và tự tính lại các chỉ số liên quan.

## Theo dõi log nghiệp vụ

Backend ghi log JSON ra stdout để Docker thu thập. Theo dõi trực tiếp:

```powershell
docker compose logs -f --tail=200 backend
```

Lọc một nhóm sự kiện trong PowerShell:

```powershell
docker compose logs backend --since=10m |
    Select-String 'liveness_|enrollment_|recognition_|attendance_'
```

Mỗi dòng có `timestamp`, `level`, `request_id`, `event`, `message` và các ID
nghiệp vụ liên quan. Header `X-Request-ID` trong response cho phép tìm toàn bộ
log của cùng request. Các sự kiện chính gồm:

- `admin_login_succeeded`, `admin_login_failed`;
- `liveness_started`, `liveness_state_changed`, `liveness_passed`;
- `enrollment_started`, `enrollment_sample_accepted`, `enrollment_completed`;
- `recognition_started`, `recognition_match_observed`, `recognition_completed`;
- `attendance_check_in_created`, `attendance_check_out_created`,
  `attendance_adjusted`;
- `worker_ready`, `worker_failed`, `unhandled_exception`.

`LOG_LEVEL=INFO` là mặc định. Request gửi frame có tần suất cao không xuất hiện
ở mức này; đặt `LOG_HTTP_FRAME_REQUESTS=true` khi cần đo từng request frame.
Không log ảnh, embedding, mật khẩu, JWT hoặc cookie.
