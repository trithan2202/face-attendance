# Kiểm thử và kịch bản demo

## Kiểm thử tự động

- Unit: normalize/centroid/matcher, quality checker, state liveness, work date, đi trễ/về sớm/tăng ca, cooldown và tính lại sau điều chỉnh.
- Integration API: login, phân quyền admin, CRUD nhân viên/ca, enrollment metadata, check-in/check-out, audit và export Excel theo ngày/tháng.
- Frontend: route guard, validation form, trạng thái kiosk và bộ lọc attendance.

## Kiểm thử webcam thủ công

- Không có mặt, nhiều hơn một mặt, ảnh mờ và người chưa đăng ký.
- Thử thách blink/quay đầu thành công và timeout/thất bại.
- Nhận diện chưa đủ frame, similarity thấp, cooldown và mất kết nối camera.
- Check-in đúng giờ/đi muộn, check-out sớm, tăng ca, ca qua ngày và sửa công có audit.

## Kịch bản demo

1. Khởi động PostgreSQL, migration, API, frontend và worker; kiểm tra health/status xanh.
2. Đăng nhập admin, tạo ca và nhân viên.
3. Mở quản trị, thực hiện thử thách liveness rồi đăng ký 10 mẫu embedding cho nhân viên.
4. Mở kiosk, giữ khuôn mặt liên tục 3 giây và ghi nhận check-in.
5. Sau khoảng thời gian cấu hình, lặp lại để check-out.
6. Mở quản trị, lọc bản ghi, điều chỉnh một bản ghi với lý do và kiểm tra audit.
7. Xuất Excel theo ngày, báo cáo công theo tháng và xác nhận không có ảnh/video xuất hiện trong DB hoặc thư mục dữ liệu.

## Definition of done

Demo được xem là hoàn thành khi toàn bộ test tự động đạt, checklist webcam qua, các script khởi động hoạt động trên Windows và kịch bản demo chạy liên tục từ đầu đến cuối mà không cần sửa trực tiếp database.
