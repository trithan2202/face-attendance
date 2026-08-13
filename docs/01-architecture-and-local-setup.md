# Kiến trúc và môi trường local

## Kiến trúc mục tiêu

```text
React/Vite (localhost) ──HTTP/WebSocket──> FastAPI ──SQLAlchemy──> PostgreSQL (Docker)
       │                                      │
       └── kiosk UI <── worker camera/local ──┴── InsightFace + MediaPipe
```

- **React + TypeScript + Vite:** frontend tiếng Việt cho kiosk và quản trị.
- **FastAPI:** API, xác thực, điều phối nghiệp vụ, health check và trạng thái worker.
- **Recognition worker:** tiến trình Python local độc lập để truy cập webcam ổn định.
- **PostgreSQL:** chạy bằng Docker Compose; chỉ database được container hóa.
- **InsightFace:** phát hiện mặt và sinh embedding; **MediaPipe Face Mesh** hỗ trợ liveness chớp mắt/quay đầu.

## Cấu hình

`.env` phải chứa database URL, camera index, ngưỡng similarity, timezone `Asia/Ho_Chi_Minh`, JWT secret, tên/mật khẩu admin ban đầu và cấu hình timeout liveness. Không commit `.env`.

## Vận hành Windows

1. Khởi động PostgreSQL bằng `docker compose up -d postgres`.
2. Cài dependencies Python và Node theo lockfile.
3. Chạy migration và seed admin/ca `HC`.
4. Chạy API, frontend và recognition worker bằng các script PowerShell riêng.
5. Mở frontend local; kiosk và trang admin dùng cùng ứng dụng nhưng route tách biệt.

## Quy ước an toàn

- API chỉ cho phép CORS từ frontend local.
- Mật khẩu admin được hash bcrypt; token JWT có hạn dùng.
- Không ghi embedding, token hay frame camera vào log.
- Worker có endpoint health/status để UI báo camera hoặc model lỗi.
