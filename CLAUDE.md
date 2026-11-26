# CLAUDE.md – Kendy Video Toolkit

Bộ công cụ dựng video dọc 9:16 độc lập cho Kendy Huyền Học. Đọc `SKILL.md` (bộ định tuyến) trước mọi việc dựng video.

## Quy tắc
1. Trả lời Kendy bằng tiếng Việt, rõ ràng, ít thuật ngữ lập trình.
2. Không phát sinh chi phí khi Kendy chưa đồng ý (không dịch vụ trả phí, không lệnh HyperFrames publish/billing/templates).
3. Không tự sửa nội dung chuyên môn (Tarot, Bát Tự Manh Phái, Tử Vi, Phong Thủy, Kinh Dịch, Nhân Tướng). Từ điển chỉ gợi ý
   chính tả; giữ nguyên ký hiệu nguồn và trạng thái 【Chờ Kendy xác nhận】.
4. Không đụng kho `Kendy-tarot` (ứng dụng Bát Tự) và Creative Studio.
5. Không đưa lên kho: video nguồn, video xuất, mô hình Whisper, `.venv`, `node_modules`, API key, mật khẩu, dữ liệu cá nhân.
6. Commit / push / tạo phiên bản chỉ khi Kendy cho phép lần đó.
7. Sửa mã: chạy `.venv/bin/python -m unittest discover -s tests` (phải đạt hết) và xem khung hình kết quả trước khi báo xong.
8. Đổi kết quả hình / tiếng mặc định (màu, vị trí, âm lượng) là thay đổi giao diện – giải thích và chờ Kendy duyệt.

## Cấu trúc
- `kvt/kvt.py` lệnh `bin/kvt` · `kvt/bo_cuc.py` bố cục an toàn, nhận diện mặt · `kvt/tu_dien.py` từ điển & đối chiếu ·
  `kvt/canh.py` ghép ảnh / cảnh · `kvt/motion.py` gọi Remotion / HyperFrames
- `presets/` phong cách (`kendy.json`) · `tu-dien/` từ điển 6 lĩnh vực · `vi-du/` cấu hình mẫu
- `motion/remotion/` intro & thẻ lá bài · `motion/hyperframes-outro/` outro
- `.claude/skills/` 9 skill (1 định tuyến + 8 chức năng) · `tests/` kiểm thử
