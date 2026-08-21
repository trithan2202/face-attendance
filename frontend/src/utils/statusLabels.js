const STATUS_LABELS_VI = {
  Active: 'Đang hoạt động',
  Inactive: 'Ngưng hoạt động',
  'Pending enrollment': 'Chờ đăng ký khuôn mặt',
  Present: 'Có mặt',
  'Missing check-in': 'Thiếu check-in',
  'Missing check-out': 'Thiếu check-out',
  Absent: 'Vắng mặt',
  'On leave': 'Nghỉ phép',
  Pending: 'Chờ duyệt',
  Approved: 'Đã duyệt',
  Rejected: 'Từ chối',
};

export const statusLabelVi = (status) => STATUS_LABELS_VI[status] || status;
