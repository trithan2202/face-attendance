# Đăng ký, nhận diện và liveness

## Enrollment

1. Quản trị viên tạo hoặc chọn nhân viên và ca.
2. Kiosk thu 10 mẫu chỉ khi có đúng một khuôn mặt, đủ lớn, detection score đạt ngưỡng và không mờ.
3. Chuẩn hóa embedding từng mẫu, tính centroid, lưu sample và centroid trong một transaction.
4. Frontend chỉ hiển thị tiến độ; không lưu frame hoặc ảnh.

Nếu người dùng hủy, camera lỗi hoặc không đủ mẫu, transaction bị rollback và giao diện báo rõ nguyên nhân.

## Liveness chủ động

Trước mỗi lần chấm công, hệ thống chọn ngẫu nhiên một thử thách: **chớp mắt**, **quay trái** hoặc **quay phải**. MediaPipe Face Mesh theo dõi landmark mắt và hướng đầu; thử thách phải hoàn thành trong timeout cấu hình, có đúng một khuôn mặt và chất lượng khung hình đạt yêu cầu.

Liveness chỉ là lớp bảo vệ demo, không được mô tả là chống giả mạo sinh trắc học hoàn toàn.

## Nhận diện và điểm danh

- Sau liveness, InsightFace tạo embedding và so cosine similarity với centroid nhân viên active.
- Cần tối thiểu 3 kết quả cùng mã trong cửa sổ 5 frame; điểm similarity phải đạt ngưỡng cấu hình.
- Worker áp dụng cooldown theo nhân viên để tránh ghi sự kiện lặp.
- Lần hợp lệ đầu tiên là `CHECK_IN`; lần tiếp theo sau `min_checkout_minutes` là `CHECK_OUT`.
- Tất cả tính toán dùng timezone `Asia/Ho_Chi_Minh`, bao gồm work date ca qua ngày, đi trễ, về sớm, tăng ca và tổng phút làm.

Các trạng thái UI tối thiểu: camera chưa sẵn sàng, không có mặt, nhiều mặt, liveness đang chờ/đạt/thất bại, không nhận diện, đã check-in, đã check-out và cooldown.
