---
name: phu-de-tieng-viet
description: Tạo phụ đề tiếng Việt tự động bằng Whisper (chạy trên máy, miễn phí) cho video Tarot dọc – SRT để sửa, ASS đẹp có tô màu từ đang nói, lọc câu ảo giác. Dùng khi cần phụ đề, caption, chữ chạy theo lời.
---

# Phụ đề tiếng Việt

```
bin/kvt phu-de VIDEO.mp4 --thu-muc RA/ [--mo-hinh turbo|small|large-v3] [--ngon-ngu vi]
               [--goi-y "tên riêng, thuật ngữ"] [--kieu tarot|toi-gian] [--khong-nhan-tu]
```
Tạo: `VIDEO.srt` (sửa tay), `VIDEO.ass` (để ghép vào video), `VIDEO.words.json` (mốc từng từ).

## Mô hình (đã đo trên giọng đọc tiếng Việt thật – FLEURS, 294 từ)
| Mô hình | Sai số từ | Tốc độ (4 lõi CPU) |
|---|---|---|
| turbo (mặc định) | ~8% | ~1,5× thời lượng |
| small | ~42% | ~0,5× thời lượng |
Chỉ dùng `small` để xem thử. Bản phát hành dùng `turbo`.

## Từ điển chuyên ngành (`tu-dien/`)
Sáu lĩnh vực: `tarot` (78 lá, tên Việt + Anh), `bat-tu-manh-phai` (cách viết theo ứng dụng Bát Tự của Kendy),
`tu-vi`, `phong-thuy`, `kinh-dich` (64 quẻ), `nhan-tuong`. Tất cả ở trạng thái 【Chờ Kendy xác nhận cách viết】.
1. Nghe đúng hơn: `bin/kvt phu-de VIDEO --linh-vuc tarot,bat-tu-manh-phai` (đưa thuật ngữ vào gợi ý Whisper).
2. Rà chính tả: tạo `VIDEO.goi-y.json` liệt kê chỗ nghi sai (sai dấu / nghi nghe nhầm). KHÔNG tự sửa.
3. Kendy duyệt: đặt `"dong_y": true` cho mục đồng ý → `bin/kvt sua-phu-de VIDEO.words.json VIDEO.goi-y.json -o RA`.
4. Có lời gốc: `bin/kvt doi-chieu VIDEO.words.json loi-goc.txt -o RA` (báo cáo khác biệt + phụ đề theo lời gốc).
Sửa / thêm thuật ngữ: chỉnh `tu-dien/tao_tu_dien.py` rồi chạy lại nó (giữ ký hiệu nguồn C / UD).
Từ điển chỉ phục vụ chính tả phụ đề, không mang nội dung lý pháp, không dùng để luận giải.

## Kiểu chữ
`--kieu kendy`: chữ kem sáng, viền xanh cổ vịt đậm, từ đang nói chuyển vàng champagne · `tarot` · `toi-gian`.

## Quy tắc
- Gợi ý từ vựng mặc định có "Kendy Huyền Học", tên chất bài, Ẩn Chính/Ẩn Phụ. Thêm tên lá bài của bài đó qua `--goi-y`.
- Bộ lọc tự bỏ câu ảo giác quen thuộc của Whisper ("Hãy subscribe cho kênh…", "Cảm ơn các bạn đã theo dõi"…)
  khi gặp nhạc/khoảng lặng. Nếu Kendy THỰC SỰ nói câu đó ở cuối video, thêm lại tay trong SRT.
- Từ có độ tin cậy < 0,4 được đếm và báo → yêu cầu Kendy đọc lại SRT trước khi xuất.
- Hiển thị: tối đa ~30 ký tự/cụm, 2 dòng, ≤ 3,2 s, không để cụm mồ côi 1–2 từ; nằm cao hơn mép dưới 430 px
  để không bị nút TikTok/Reels che. Phông Be Vietnam Pro (đủ dấu tiếng Việt, giấy phép OFL).
- Phụ đề là lời Kendy nói – không tự sửa nội dung, chỉ sửa lỗi nhận dạng khi Kendy xác nhận.
