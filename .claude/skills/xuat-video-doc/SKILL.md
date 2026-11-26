---
name: xuat-video-doc
description: Xuất MP4 dọc 9:16 1080×1920 chuẩn đăng TikTok, Reels, YouTube Shorts (H.264 High, 30 fps cố định, AAC 48 kHz, faststart) và tự kiểm tra thông số. Dùng khi xuất video cuối cùng hoặc kiểm tra tệp trước khi đăng.
---

# Xuất video dọc

```
bin/kvt xuat VAO.mp4 -o RA.mp4 [tham số khung/màu/nét/phụ đề/lá bài/nhạc] [--intro I.mp4] [--outro O.mp4]
             [--fps 30] [--crf 18] [--preset slow]
bin/kvt kiem-tra RA.mp4
```

## Thông số đầu ra
- 1080×1920, SAR 1:1, H.264 High@4.2, yuv420p, BT.709, CRF 18 (preset slow), GOP 2 s, khung hình cố định.
- 29,97 fps → 30 fps; nguồn 60 fps giữ 60 (truyền `--fps 60`). Không nội suy khung (tránh hình nhoè, méo).
- AAC 192 kb/s, 48 kHz, stereo, −14 LUFS. `+faststart` để phát ngay trên điện thoại.
- Dung lượng ~9–12 MB/phút·10 → 1 phút ≈ 60–75 MB. Muốn nhẹ hơn: `--crf 20`.

## Vùng an toàn (TikTok / Reels / Shorts)
Trên 230 px, dưới 420 px, phải 150 px dành cho giao diện ứng dụng. Phụ đề nằm trong dải 1290–1510 px, lề phải 150 px.
Lá bài, điểm nhấn, CTA tự đặt trong vùng an toàn (xem `kvt/bo_cuc.py`).

## Kiểm tra bắt buộc trước khi báo xong
1. `bin/kvt kiem-tra RA.mp4` → `"dat": true`.
2. Xem 3 khung hình: đầu (intro), giữa (phụ đề + lá bài), cuối (outro).
3. Nghe đoạn có nhạc nền: nhạc không lấn giọng.
4. Đọc `RA.bo-cuc.json`: mục nào `"khong_che": false` phải xem khung hình tương ứng.
Báo Kendy trung thực phần đã kiểm và chưa kiểm (ví dụ: chưa xem trên điện thoại thật).
