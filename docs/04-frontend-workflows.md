# Luồng giao diện

## Kiosk `/kiosk`

Màn hình toàn trang hiển thị webcam, chỉ dẫn liveness, trạng thái nhận diện và thông báo kết quả lớn. Kiosk không có quyền quản trị; nút thoát/quay lại admin không xuất hiện trong giao diện công khai.

Luồng: sẵn sàng camera → một khuôn mặt → thử thách liveness → xác nhận nhận diện → hiển thị check-in/check-out hoặc lỗi → quay về trạng thái chờ.

## Đăng nhập `/login`

Form username/password, hiển thị lỗi chung khi đăng nhập sai. Token được lưu theo cơ chế an toàn cho demo local; logout xóa session.

## Quản trị

- **Dashboard:** số lượt check-in/check-out hôm nay, nhân viên đi muộn, thiếu check-out và sự kiện gần nhất.
- **Nhân viên:** tìm kiếm, CRUD, phòng ban, ca, trạng thái active/inactive, khởi tạo đăng ký lại khuôn mặt.
- **Ca làm:** CRUD mã/tên ca, giờ bắt đầu/kết thúc, grace period và cờ qua ngày.
- **Chấm công:** lọc ngày, nhân viên, phòng ban và trạng thái; xem daily record/event; sửa thời gian hoặc trạng thái với lý do bắt buộc; xem audit; xuất CSV.

## Trải nghiệm lỗi

Mọi thao tác có loading, thông báo thành công/thất bại, validation phía client và thông điệp API. Camera/model/DB không sẵn sàng phải có hướng dẫn hành động, không chỉ hiển thị lỗi kỹ thuật.
