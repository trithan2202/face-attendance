# Phạm vi sản phẩm

## Mục tiêu

Tạo demo điểm danh khuôn mặt chạy hoàn toàn trên một máy Windows. Người quản trị dùng giao diện web local để quản lý nhân viên, ca làm và dữ liệu công; nhân viên dùng màn hình kiosk để đăng ký hoặc chấm công bằng webcam.

## Vai trò

- **Quản trị viên:** đăng nhập, quản lý nhân viên/ca, đăng ký lại khuôn mặt, theo dõi và điều chỉnh chấm công, xuất CSV.
- **Kiosk:** không cần đăng nhập; chỉ hiển thị camera, thử thách liveness và kết quả nhận diện.

## Chức năng bắt buộc

- Đăng nhập bằng một tài khoản quản trị local.
- CRUD nhân viên và ca làm, bao gồm ca qua ngày và các khoảng cho phép đi trễ/về sớm.
- Đăng ký 10 embedding mẫu, tạo centroid và chỉ kích hoạt hồ sơ khi đăng ký hoàn tất.
- Chấm công vào/ra qua webcam; nhận diện chỉ được chấp nhận sau liveness và nhận diện ổn định.
- Xem, lọc, chỉnh sửa thủ công dữ liệu chấm công. Mỗi sửa đổi bắt buộc có lý do và có audit log.
- Xuất CSV theo bộ lọc hiện tại.

## Không thuộc phạm vi demo

- Cloud, mobile app, nhận diện nhiều camera hoặc nhiều kiosk đồng thời.
- Quy trình nhân viên gửi đơn điều chỉnh/duyệt đơn.
- Liveness/anti-spoofing cấp độ bảo mật sinh trắc học cao.
- Lưu ảnh, video hoặc frame webcam; hệ thống chỉ lưu embedding.

## Tiêu chí nghiệm thu

Một máy Windows mới có thể chạy PostgreSQL qua Docker, khởi tạo dữ liệu, đăng nhập quản trị, đăng ký một nhân viên, hoàn thành liveness, ghi nhận check-in/check-out và xuất báo cáo CSV.
