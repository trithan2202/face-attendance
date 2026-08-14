# Face Attendance

Hệ thống chấm công bằng khuôn mặt chạy local, gồm kiosk nhận diện trên trình duyệt và trang quản trị nhân viên, ca làm việc, dữ liệu chấm công, audit trail và báo cáo Excel.

## Mục lục

- [Tính năng chính](#tính-năng-chính)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Workflow nghiệp vụ](#workflow-nghiệp-vụ)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Chạy nhanh bằng Docker](#chạy-nhanh-bằng-docker)
- [Chạy ở chế độ phát triển](#chạy-ở-chế-độ-phát-triển)
- [Kiểm thử](#kiểm-thử)
- [API và các địa chỉ truy cập](#api-và-các-địa-chỉ-truy-cập)
- [Vận hành và xử lý lỗi](#vận-hành-và-xử-lý-lỗi)
- [Bảo mật và giới hạn](#bảo-mật-và-giới-hạn)

## Tính năng chính

- Đăng nhập quản trị bằng JWT lưu trong cookie `HttpOnly`.
- Quản lý nhân viên, phòng ban, ca làm việc và trạng thái hoạt động.
- Đăng ký khuôn mặt bằng webcam với thử thách liveness.
- Kiosk nhận diện không yêu cầu đăng nhập và không chạy liveness.
- Chỉ ghi check-in/check-out khi cùng một khuôn mặt được nhận diện liên tục trong 3 giây.
- Hỗ trợ ca qua ngày, đi muộn, về sớm, tăng ca và giới hạn check-out quá sớm.
- Điều chỉnh chấm công có lý do bắt buộc và lưu audit trail trước/sau.
- Xuất Excel theo ngày và báo cáo tháng gồm bảng công cùng sheet `Công OT`.

## Công nghệ sử dụng

| Thành phần | Công nghệ |
| --- | --- |
| Frontend | React 18, Vite, React Router, Tailwind CSS, Headless UI |
| Backend API | FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Face recognition | InsightFace, ONNX Runtime, OpenCV |
| Liveness | MediaPipe Face Mesh |
| Báo cáo | OpenPyXL, Excel `.xlsx` |
| Xác thực | bcrypt, JWT, cookie `HttpOnly` |
| Triển khai local | Docker Compose, Nginx |
| Kiểm thử | Python `unittest`, FastAPI TestClient |

## Kiến trúc hệ thống

### Các lớp chính

1. **Presentation:** React cung cấp `/kiosk`, `/login` và các màn hình quản trị.
2. **Reverse proxy:** Nginx phục vụ frontend production và chuyển `/api` đến FastAPI.
3. **API:** FastAPI xác thực, kiểm tra request, quản lý session và trả response thống nhất.
4. **Domain services:** xử lý enrollment, liveness, recognition, attendance, audit và export.
5. **Face engine:** phát hiện khuôn mặt, kiểm tra chất lượng, tạo embedding và so khớp centroid.
6. **Persistence:** repository SQLAlchemy truy cập PostgreSQL; Alembic quản lý schema.
7. **Observability:** backend ghi log JSON có `request_id` và event nghiệp vụ.

## Cấu trúc thư mục

```text
face-attendance/
├── attendance/                 # Tính ngày công, check-in/out và các chỉ số
├── backend/app/
│   ├── api/                    # System, auth, kiosk và admin routes
│   ├── core/                   # Config, database, JWT, logging
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Truy cập dữ liệu
│   ├── schemas/                # Pydantic request/response
│   └── services/               # Enrollment, liveness, recognition, report
├── camera/                     # Desktop recognition worker tùy chọn
├── face_engine/                # Detection, recognition, quality, matching
├── frontend/                   # React/Vite SPA và Nginx config
├── migrations/                 # Alembic migrations
├── scripts/                    # Bootstrap, seed và script chạy Windows
├── tests/                      # Unit/integration tests
├── docs/                       # Đặc tả chi tiết theo chủ đề
├── docker-compose.yml
└── requirements.txt
```

## Chạy nhanh bằng Docker

Đây là cách chạy được khuyến nghị để demo toàn bộ hệ thống.

### Yêu cầu

- Windows 10/11 với Docker Desktop đang chạy.
- Docker Compose v2.
- Webcam và trình duyệt cho phép truy cập camera.
- Các cổng `3000`, `8000` và `5432` chưa bị ứng dụng khác chiếm dụng.

### Bước 1: build và khởi động

```powershell
docker compose up -d --build
docker compose ps
```

### Bước 2: truy cập ứng dụng

| Chức năng | Địa chỉ |
| --- | --- |
| Kiosk | `http://localhost:3000/kiosk` |
| Đăng nhập admin | `http://localhost:3000/login` |
| Dashboard | `http://localhost:3000/admin/dashboard` |
| API docs | `http://localhost:8000/api/docs` |
| API health | `http://localhost:8000/api/health` |
| PostgreSQL | `localhost:5432` |

Đăng nhập bằng `ADMIN_USERNAME` và `ADMIN_PASSWORD` trong `.env`. Khi mở kiosk hoặc enrollment, chọn **Allow** khi trình duyệt yêu cầu quyền camera.

### Dừng hệ thống

```powershell
docker compose down
```

## API và các địa chỉ truy cập

Các nhóm API chính:

- `/api/health`, `/api/worker/status`
- `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`
- `/api/admin/shifts`
- `/api/admin/employees`
- `/api/admin/enrollment`
- `/api/admin/attendance`
- `/api/kiosk/recognition`
- `/api/kiosk/liveness` — route tương thích và kiểm thử liveness độc lập

Swagger/OpenAPI đầy đủ tại `http://localhost:8000/api/docs`.

## Bảo mật và giới hạn

- Đây là hệ thống demo/local, chưa được thiết kế để mở trực tiếp ra Internet.
- Liveness hiện tại là kiểm tra hành động bằng MediaPipe, không phải anti-spoofing sinh trắc học cấp cao.
- Embedding khuôn mặt vẫn là dữ liệu sinh trắc học nhạy cảm và phải được bảo vệ như dữ liệu cá nhân.
- Session enrollment/recognition được giữ trong RAM và mất khi backend restart.
- Chưa có rate limit cho kiosk public, phân quyền nhiều vai trò, HA hoặc session store dùng chung.
