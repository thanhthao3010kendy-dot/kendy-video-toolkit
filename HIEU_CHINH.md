# Nhật ký hiệu chỉnh bằng video thật

Ghi theo mẫu ở `QUY_TRINH_HIEU_CHINH.md` mục D.

## Video 1 – 1000037183.mp4 (ChatGPT chạy thử v1.0.0, 26/11/2026)
- Nguồn: 720×1280, MP4, 50,27 s. Cảnh trải bài trên khăn tối, không có mặt người; ám vàng; video có sẵn hiệu ứng
  tia sáng / lấp lánh và chữ "Kendy huyền học" ở dưới (theo khung hình 1000037186.png Kendy gửi).
- ChatGPT (v1.0.0): dò khoảng lặng được, ngưỡng tự động −37 dB, giữ 7 đoạn → dự kiến 39,70 s.
  Không chạy được: nhận diện mặt (thiếu YuNet), phụ đề (thiếu Whisper), màu / nét chưa xong, xuất MP4 hết thời gian.
- Claude: chưa nhận được video; thử cân bằng trắng trên khung hình 1000037186.png: R×0,98 B×1,05 (giảm ám vàng).
- v1.0.1-beta xử lý các điểm trên (YuNet đóng gói, phụ đề không Whisper, xuất chia đoạn). CHƯA nghiệm thu.
