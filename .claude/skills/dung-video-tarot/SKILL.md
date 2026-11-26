---
name: dung-video-tarot
description: Quy trình tổng dựng video Tarot dọc 9:16 (1080×1920) cho Kendy Huyền Học – cắt khoảng lặng, đồng bộ lời thoại, phụ đề tiếng Việt, chỉnh màu, độ nét, lá bài sắc nét, motion graphics, nhạc nền, xuất MP4. Dùng khi Kendy đưa video thô và muốn video hoàn chỉnh, hoặc hỏi "dựng video", "làm reels/shorts/tiktok tarot".
---

# Dựng video Tarot dọc – quy trình tổng

Mọi lệnh chạy trong thư mục `kendy-video-toolkit/`. Bộ công cụ độc lập: KHÔNG sửa Creative Studio,
KHÔNG đụng ứng dụng Bát Tự (kho `Kendy-tarot`). Tất cả chạy trên máy, miễn phí. Không gọi dịch vụ trả phí
(HeyGen, HyperFrames publish/billing/templates Pro, API AI trả tiền) khi Kendy chưa đồng ý.

Định tuyến tổng: đọc `SKILL.md` ở gốc kho (skill `kendy-video`) trước.

## Ưu tiên chất lượng (theo Kendy)
1. Video mượt: khung hình cố định 30 fps (hoặc giữ 60 nếu quay 60), không nội suy khung giả.
2. Lá bài sắc nét: chèn ẢNH GỐC lá bài (`--la-bai`) thay vì phóng to hình quay; độ nét mặc định "nhe".
3. Hiệu ứng vừa phải: mờ dần 0,3 s, tô màu từ đang nói, không nảy/rung/xoay liên tục.
4. Âm thanh tự nhiên: khử ồn nhẹ, nén nhẹ, −14 LUFS, nhạc nền −22 dB tự hạ khi nói.

## Các bước
1. Kiểm tra đầu vào: `bin/kvt probe VIDEO` (độ phân giải, fps, có âm thanh không, có xoay không).
2. (Nếu có micro rời) skill `dong-bo-loi-thoai`.
3. Cắt khoảng lặng – skill `cat-khoang-lang`. Xem trước bằng `--chi-xem`.
4. Phụ đề – skill `phu-de-tieng-viet`. LUÔN nhắc Kendy đọc lại SRT (Whisper có thể nghe sai thuật ngữ).
5. Màu, độ nét, khung 9:16 – skill `mau-va-do-net`. Xem 2–3 khung hình trước khi xuất cả bài.
6. Motion graphics (intro, thẻ lá bài, outro) – skill `motion-graphics-tarot`.
7. Âm thanh + nhạc nền – skill `am-thanh-nhac-nen`.
8. Xuất + kiểm tra – skill `xuat-video-doc`.

## Chạy một lệnh
Sao chép mẫu trong `vi-du/`, sửa đường dẫn, rồi: `bin/kvt dung du-an.json`.
- `vi-du/du-an-mau.json` – video quay thật, phong cách Kendy.
- `vi-du/anh-va-long-tieng.json` – ảnh lá bài + video ngắn + file lồng tiếng WAV/MP3.
- `vi-du/video-long-tieng.json` – video + lồng tiếng thu sau (thay tiếng gốc).
`"phong_cach": "kendy"` nạp `presets/kendy.json` (xanh cổ vịt đậm, kem sáng, vàng champagne; sáng, nét; lá bài viền
champagne; intro/outro tắt; CTA tuỳ chọn). Mục nào ghi trong cấu hình dự án sẽ ghi đè phong cách.
Thứ tự nội bộ: (ghép cảnh / lồng tiếng / đồng bộ) → cắt lặng → phụ đề (+ từ điển, + lời gốc) → âm thanh →
hình + lá bài + điểm nhấn + CTA + phụ đề → (intro/outro nếu có) → kiểm tra.

## Các mục cấu hình hay dùng
- `"la_bai": [{"anh": "...", "bat_dau": 6, "ket_thuc": 12}]` – ảnh lá bài sắc nét, tự đặt tránh mặt.
- `"diem_nhan": [{"chu": "...", "phu": "...", "bat_dau": 20, "ket_thuc": 24}]` – CHỈ ở nội dung quan trọng Kendy chỉ định.
- `"cta": {"chu": "Theo dõi Kendy Huyền Học", "phu": "…", "giay": 3.5}` – lời kêu gọi cuối video; `null` để tắt.
- `"vung_tranh": [{"x":..,"y":..,"rong":..,"cao":..,"bat_dau":..,"ket_thuc":..}]` – vùng không được che
  (ví dụ chỗ Kendy hay cầm bài); toạ độ trên khung 1080×1920.
- `"intro"`/`"outro"`: đường dẫn tệp, hoặc `{"tao": true, "tieu_de": "...", "anh": "..."}` để tự dựng, hoặc `null`.
- `"loi_goc": "loi-thoai.txt"` – phụ đề dùng đúng lời gốc Kendy viết.

## Thời gian xử lý (máy 4 lõi CPU, không GPU)
- Cắt lặng ~0,5× thời lượng; phụ đề turbo ~1,5× thời lượng (small ~0,5×); xuất 9:16 preset slow ~3× thời lượng.
- Cần nhanh để xem thử: `--preset veryfast` và phụ đề `--mo-hinh small`.

## Nội dung chuyên môn
Lời thoại/ý nghĩa lá bài do Kendy cung cấp. Không tự viết thông điệp Tarot hay lời bình gán cho Kendy.
Chữ trên màn hình (tiêu đề, tên lá bài, lời kêu gọi) phải lấy từ Kendy hoặc hỏi lại.
