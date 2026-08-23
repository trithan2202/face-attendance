/**
 * Đổi số phút sang chuỗi hh:mm.
 *
 * Dùng cho thời gian tăng ca để khớp với cách đọc giờ công trên bảng lương,
 * thay vì bắt người xem tự nhẩm "135 phút" ra "2 giờ 15".
 */
export const formatDuration = (minutes) => {
  const total = Math.max(0, Math.round(Number(minutes) || 0));
  const hours = Math.floor(total / 60);
  const rest = total % 60;

  return `${String(hours).padStart(2, '0')}:${String(rest).padStart(2, '0')}`;
};
