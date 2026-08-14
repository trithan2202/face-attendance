# Face Attendance — Project Status

**Cập nhật lần cuối:** 14/08/2026  
**Phiên bản API:** `0.1.0`  
**Trạng thái:** Hoàn thiện luồng demo local; cần kiểm thử webcam thực tế và gia cố trước khi triển khai production.

## 1. Tổng quan hiện trạng

Hệ thống hiện chạy đầy đủ bằng Docker Compose với ba service:

- `postgres`: PostgreSQL 16 và persistent volume.
- `backend`: FastAPI, face engine, migration/seed tự động và API report.
- `frontend`: React production build được phục vụ bằng Nginx.

Luồng nghiệp vụ chính đã kết nối với database và API thật. Frontend không còn dùng mock/localStorage cho các chức năng quản trị, enrollment, recognition hoặc attendance.

## 2. Kiến trúc đang sử dụng

```text
Browser webcam
    ↓
React/Vite SPA
    ↓ /api
Nginx (production) hoặc Vite proxy (development)
    ↓
FastAPI routes
    ↓
Domain services
    ├── Enrollment + liveness
    ├── Recognition + attendance
    ├── Adjustment + audit
    └── Excel reporting
    ↓
Repositories / SQLAlchemy
    ↓
PostgreSQL / Alembic
```

InsightFace, ONNX Runtime và OpenCV xử lý phát hiện/embedding/so khớp khuôn mặt. MediaPipe Face Mesh xử lý thử thách liveness. Session enrollment và recognition được lưu trong RAM của backend.

Desktop recognition worker trong `camera/` hiện là công cụ tùy chọn để kiểm tra model, camera và heartbeat; kiosk web là luồng chấm công chính.

## 3. Hạng mục đã hoàn thành

### Nền tảng và vận hành

- [x] FastAPI app, CORS, response lỗi thống nhất và Swagger/OpenAPI.
- [x] Docker Compose cho PostgreSQL, backend và frontend.
- [x] Healthcheck database/backend và dependency startup giữa các service.
- [x] Bootstrap database tự động khi backend Docker khởi động.
- [x] Alembic migration `0001` đến `0003`.
- [x] Tự nhận biết và tiếp quản schema legacy năm bảng.
- [x] Seed tài khoản admin và ca mặc định có tính lặp lại an toàn.
- [x] Log JSON có `request_id` và event nghiệp vụ.
- [x] Worker heartbeat với trạng thái `STARTING`, `READY`, `ERROR`, `STOPPED`.

### Database

Các bảng hiện có:

1. `admin_users`
2. `shifts`
3. `employees`
4. `face_embeddings`
5. `attendance_events`
6. `attendance_daily`
7. `attendance_adjustments`

Đã có ràng buộc duy nhất cho mã ca, mã nhân viên và cặp `(employee_id, work_date)`.

### Xác thực admin

- [x] Hash mật khẩu bằng bcrypt.
- [x] JWT access token có thời hạn cấu hình được.
- [x] Cookie `HttpOnly`, `SameSite=Lax`.
- [x] Khôi phục phiên qua `GET /api/auth/me`.
- [x] Bảo vệ toàn bộ `/api/admin/*` bằng dependency xác thực.
- [x] Từ chối seed mật khẩu admin mặc định không an toàn.

### Quản lý ca làm việc

- [x] Danh sách, thêm, sửa và xóa ca.
- [x] Hỗ trợ ca qua ngày.
- [x] Grace period đi muộn/về sớm.
- [x] Không cho xóa ca đang được gán cho nhân viên.
- [x] Nút xóa trên giao diện luôn màu đỏ, không phụ thuộc hover.

### Quản lý nhân viên

- [x] Danh sách, tìm kiếm, lọc, thêm, sửa và chuyển `INACTIVE`.
- [x] Mã nhân viên duy nhất.
- [x] Khi mở `Add Employee`, frontend tự sinh mã `A` + 6 chữ số.
- [x] Nhân viên mới bắt đầu ở trạng thái `PENDING_ENROLLMENT`.
- [x] Chỉ chuyển `ACTIVE` sau khi đăng ký đủ dữ liệu khuôn mặt.
- [x] Xóa nhân viên là soft delete để bảo toàn lịch sử chấm công.
- [x] Nút xóa và nút xác nhận `Delete` luôn hiển thị màu đỏ.

### Enrollment và liveness

- [x] Enrollment session theo từng nhân viên.
- [x] Bắt buộc vượt qua liveness trước khi thu embedding.
- [x] Thử thách ngẫu nhiên `BLINK`, `TURN_LEFT`, `TURN_RIGHT`.
- [x] Kiểm tra timeout, định dạng frame, kích thước file và số khuôn mặt.
- [x] Kiểm tra detection score, kích thước khuôn mặt và độ mờ.
- [x] Thu 10 embedding trong RAM và tạo một centroid.
- [x] Thay dữ liệu khuôn mặt cũ và kích hoạt nhân viên trong một transaction.
- [x] Không lưu ảnh/frame xuống filesystem hoặc database.
- [x] Preview enrollment được phản chiếu như gương; frame backend không bị lật.

### Recognition và attendance

- [x] Kiosk recognition không yêu cầu đăng nhập và không chạy liveness.
- [x] Chỉ so khớp centroid của nhân viên `ACTIVE`.
- [x] Yêu cầu cùng một khuôn mặt liên tục trong 3 giây.
- [x] Reset bộ đếm khi mất mặt, nhiều mặt, đổi người hoặc frame gián đoạn.
- [x] Ghi `CHECK_IN` cho lần hợp lệ đầu tiên của `work_date`.
- [x] Ghi `CHECK_OUT` sau thời gian tối thiểu cấu hình.
- [x] Ngăn sự kiện trùng bằng trạng thái cooldown.
- [x] Hỗ trợ ca qua ngày bằng `WorkDateResolver`.
- [x] Tính worked, late, early leave và overtime minutes.

### Quản trị chấm công và audit

- [x] Lọc theo ngày, nhân viên, phòng ban và trạng thái.
- [x] Xem daily record và các attendance event liên quan.
- [x] Điều chỉnh giờ vào, giờ ra hoặc trạng thái với lý do bắt buộc.
- [x] Khóa bản ghi trong quá trình điều chỉnh.
- [x] Tự tính lại các chỉ số sau điều chỉnh.
- [x] Lưu admin, lý do, snapshot trước/sau và timestamp.
- [x] Modal Audit Trail đã tăng chiều rộng thêm 100px, lên 548px.

### Báo cáo Excel

- [x] Đã thay export CSV bằng Excel `.xlsx` theo ngày.
- [x] Báo cáo tháng có sheet bảng công nhân viên theo từng ngày.
- [x] Báo cáo tháng có sheet thứ hai tên `Công OT`.
- [x] Sheet OT đã bỏ cột dự án và đổi `VỊ TRÍ` thành `PHÒNG BAN`.
- [x] Chỉ tạo cột cho `work_date` có `overtime_minutes > 0`.
- [x] Ngày OT được loại trùng, sắp tăng dần và lưu dưới dạng date của Excel.
- [x] Giờ OT được quy đổi từ phút sang giờ; `Total` dùng công thức Excel.
- [x] Có thông báo rõ ràng khi tháng không có dữ liệu OT.

### Frontend

- [x] Các route `/kiosk`, `/login`, `/admin/dashboard`, `/admin/employees`, `/admin/shifts`, `/admin/attendance`.
- [x] AuthContext dùng cookie và API thật.
- [x] Kiosk webcam hiển thị tiến độ giữ khuôn mặt 3 giây.
- [x] Enrollment webcam hiển thị liveness và tiến độ 10 mẫu.
- [x] Form và thông báo có loading/error/success state.
- [x] Download Excel theo ngày và theo tháng.
- [x] Production build qua Docker/Nginx.

## 4. API đã triển khai

### System và auth

- `GET /api/health`
- `GET /api/worker/status`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Admin

- `GET|POST /api/admin/shifts`
- `GET|PUT|DELETE /api/admin/shifts/{shift_id}`
- `GET|POST /api/admin/employees`
- `GET|PUT|DELETE /api/admin/employees/{employee_id}`
- `POST /api/admin/employees/{employee_id}/enrollment`
- `GET|DELETE /api/admin/enrollment/{session_id}`
- `POST /api/admin/enrollment/{session_id}/frame`
- `GET /api/admin/attendance`
- `GET /api/admin/attendance/export.xlsx`
- `GET /api/admin/attendance/export-monthly.xlsx`
- `GET|PATCH /api/admin/attendance/{daily_id}`
- `GET /api/admin/attendance/{daily_id}/adjustments`

### Kiosk

- `POST|GET /api/kiosk/recognition...`
- `POST /api/kiosk/recognition/{session_id}/frame`
- Các route `/api/kiosk/liveness...` được giữ để tương thích và kiểm thử liveness độc lập.

Chi tiết request/response được sinh tự động tại `/api/docs`.

## 5. Trạng thái kiểm thử

Lần kiểm tra gần nhất:

| Kiểm tra | Kết quả |
| --- | --- |
| Backend unit/integration tests | 22/22 passed |
| Attendance và Excel integration tests | Passed |
| Kiểm thử ngày `OT = 0` không tạo cột | Passed |
| Recognition giữ mặt 3 giây/reset frame gap | Passed |
| Enrollment 10 mẫu + centroid | Passed |
| Liveness blink/quay đầu/timeout | Passed |
| Auth và CRUD API | Passed |
| Docker frontend production build | Passed |
| Frontend HTTP tại cổng 3000 | HTTP 200 |
| `git diff --check` | Passed; chỉ có cảnh báo line ending trên Windows |

Lệnh chạy backend test:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Lệnh build frontend:

```powershell
docker compose build frontend
```

## 6. Hướng dẫn chạy nhanh

```powershell
Copy-Item .env.example .env
# Sửa JWT_SECRET, ADMIN_USERNAME và ADMIN_PASSWORD

docker compose up -d --build
docker compose ps
docker compose logs -f --tail=200 backend
```

Địa chỉ sử dụng:

- Kiosk: `http://localhost:3000/kiosk`
- Admin login: `http://localhost:3000/login`
- API docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/api/health`

Hướng dẫn đầy đủ và workflow xem tại [README.md](./README.md).

## 7. Hạn chế và rủi ro còn lại

### Chức năng và trải nghiệm

- Chưa có automated end-to-end test sử dụng webcam thật.
- Giao diện còn trộn tiếng Anh và tiếng Việt; cần thống nhất bản địa hóa.
- Dashboard hiện sử dụng các API tổng hợp hiện có; chưa có endpoint dashboard chuyên biệt.
- Chưa có công cụ quản trị để xóa riêng embedding hoặc reset enrollment hàng loạt.

### Face recognition và liveness

- Liveness hiện là kiểm tra hành động, chưa chống ảnh/video replay ở mức production.
- Độ chính xác cần được hiệu chỉnh bằng camera, ánh sáng và dữ liệu người dùng thực tế.
- Session lưu trong RAM nên mất khi backend restart và không dùng chung giữa nhiều instance.
- Face model tải trong process backend; cần đánh giá RAM/CPU/GPU khi có nhiều kiosk đồng thời.

### Bảo mật và dữ liệu

- Kiosk API đang public trong mạng local và chưa có rate limit.
- Chỉ có một vai trò admin, chưa có RBAC.
- Embedding chưa có encryption riêng ở mức cột/database.
- Cần rà soát và loại bỏ dữ liệu ảnh mẫu trong repo trước khi bàn giao chính thức.
- Không được commit `.env`, JWT secret hoặc mật khẩu thật.

### Kỹ thuật và vận hành

- Một số model còn dùng `datetime.utcnow()` và phát sinh deprecation warning; nên chuyển sang timestamp timezone-aware.
- Console Windows mã hóa CP1252 có thể báo lỗi khi ghi log tiếng Việt, dù test vẫn pass.
- Chưa có CI/CD, backup/restore tự động, monitoring tập trung hoặc cảnh báo production.
- Desktop worker cũ chưa tham gia luồng chấm công web và có thể được tách thành công cụ diagnostics riêng.

## 8. Ưu tiên tiếp theo

1. Chạy demo end-to-end bằng webcam thật: tạo nhân viên → liveness → enrollment → check-in → check-out → export.
2. Hiệu chỉnh threshold, chất lượng frame và liveness theo điều kiện camera thực tế.
3. Bổ sung E2E test frontend và test report bằng dữ liệu nhiều nhân viên/ca qua ngày.
4. Chuẩn hóa toàn bộ UI sang một ngôn ngữ.
5. Gia cố bảo mật: rate limit kiosk, RBAC, HTTPS và chính sách bảo vệ embedding.
6. Chuyển session in-memory sang Redis nếu cần chạy nhiều backend instance.
7. Thiết lập CI, backup PostgreSQL và giám sát vận hành.

## 9. Tiêu chí sẵn sàng bàn giao demo

- [ ] Thay toàn bộ secret/mật khẩu mặc định trong `.env`.
- [ ] Xác nhận Docker Desktop tự khởi động và ba service healthy.
- [ ] Test camera trên đúng máy demo và đúng trình duyệt.
- [ ] Đăng ký lại ít nhất hai nhân viên với điều kiện ánh sáng khác nhau.
- [ ] Test check-in/check-out và giới hạn 3 giây.
- [ ] Test ca thường, ca qua ngày và dữ liệu OT.
- [ ] Mở được hai sheet trong báo cáo tháng và kiểm tra công thức `Total`.
- [ ] Kiểm tra audit trail sau khi điều chỉnh dữ liệu.
- [ ] Xác nhận không có ảnh/frame nhạy cảm được ghi ra ổ đĩa.
- [ ] Sao lưu PostgreSQL volume trước buổi demo quan trọng.
