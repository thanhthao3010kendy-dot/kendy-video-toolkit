# Báo cáo cài đặt & kiểm thử – 26/11/2026

Môi trường thử: máy ảo đám mây Linux, 4 lõi CPU, 15 GB RAM, **không GPU**. Chưa thử trên máy của Kendy
hay điện thoại thật.

## 1. Kiểm tra trước khi cài

| Công cụ | Giấy phép | Tương thích | Phần cứng | Kết luận |
|---|---|---|---|---|
| FFmpeg 6.1.1 | LGPL/GPL (bản Ubuntu dựng GPL) – dùng tự do, chỉ ràng buộc khi phát hành lại phần mềm | Có đủ libx264, libass, zscale, cas, loudnorm, sidechaincompress | CPU bất kỳ | Có sẵn, dùng ngay |
| Whisper | MIT | Python 3.13 + PyTorch 2.15 CPU | CPU chạy được; turbo cần ~3 GB RAM | Cài bản CPU (nhẹ, không cần GPU) |
| yt-dlp | Unlicense (phạm vi công cộng) | Python | Không đáng kể | Cài |
| Remotion 4.0.542 | Remotion License: **miễn phí** cho cá nhân / tổ chức ≤ 3 nhân viên, kể cả thương mại; lớn hơn phải mua Company License | Node 22, cần Chrome headless | ~1 GB RAM khi dựng | Cài – Kendy dùng cá nhân thuộc diện miễn phí |
| HyperFrames 0.9.27 | Apache-2.0 (mã nguồn). Một số lệnh gắn dịch vụ HeyGen có thể tính phí (publish, billing, templates Pro) | Node ≥ 22, FFmpeg, Chrome | ~256 MB RAM/luồng | Cài, **tắt telemetry**, khoá các lệnh có thể tính phí |

Chọn phiên bản đã phát hành ≥ 2 tuần (tránh bản mới chưa ổn định). Không cài gì vào kho `Kendy-tarot`.

## 2. Kết quả từng công cụ

| Công cụ | Đã cài | Hoạt động | Bằng chứng |
|---|---|---|---|
| FFmpeg | ✅ (có sẵn) | ✅ | Toàn bộ cắt / màu / nét / phụ đề / nhạc / xuất chạy được |
| Whisper | ✅ | ✅ | Tiếng Việt thật (FLEURS): **turbo sai 7,8–8,5% số từ**, small sai 42%. Tiếng Anh: video Tarot thật |
| yt-dlp | ✅ | ⚠️ Một phần | Tải được từ archive.org (video Tarot 1080p, cắt đoạn 90 s). **YouTube chặn** từ máy chủ đám mây ("Sign in to confirm you're not a bot") – trên máy Kendy thường tải được; cần cookie trình duyệt nếu bị chặn |
| Remotion | ✅ | ✅ | Dựng `TarotIntro` 3,5 s (27 s) và `LaBaiReveal` 4 s, 1080×1920, chữ Việt đủ dấu |
| HyperFrames | ✅ | ✅ (dựng cục bộ) | `check` đạt, dựng outro 4 s trong 13 s. Thành phần phụ chưa cài (không cần): whisper-cpp, Kokoro TTS, MusicGen, Docker |

## 3. Dữ liệu thử thật
- Video Tarot tiếng Anh 1080p (người đọc bài cầm lá bài, có nhạc nền), archive.org, nhãn Public Domain Mark – chỉ dùng thử, không phát hành.
- Giọng đọc tiếng Việt thật: Google FLEURS `vi_vn` (CC-BY 4.0), 10 câu, ghép thành bài nói 137 s có khoảng nghỉ, lồng lên hình video Tarot.
- Ảnh lá bài The Moon, Rider-Waite-Smith 1909 (phạm vi công cộng), Wikimedia Commons.
- Nhạc nền thử: âm tổng hợp bằng FFmpeg (không bản quyền) – chỉ để kiểm thử.

## 4. Kết quả từng chức năng

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Cắt khoảng lặng | ✅ Giữ đủ 10/10 câu, bỏ 38 s / 137 s, lệch hình–tiếng 0,5 ms | **Lỗi phát hiện & đã sửa**: bản đầu dùng ngưỡng cố định −38 dB làm mất 2 câu nói nhỏ. Nay tự tính ngưỡng theo từng video |
| Cắt theo lời nói (Whisper) | ✅ | Dùng cho video có nhạc nền liên tục (cách dò âm lượng không cắt được – đã thấy trên video tiếng Anh) |
| Đồng bộ micro rời | ✅ Tìm đúng +437 ms và −1250 ms; sau ghép đo lại 0 ms | Âm thanh không liên quan → cảnh báo độ tin cậy thấp (đúng) |
| Phụ đề | ✅ SRT + ASS tô màu từng từ | Lọc câu ảo giác "Hãy subscribe cho kênh…" (đã gặp thật khi thử đoạn chỉ có nhạc) |
| Chỉnh màu / độ nét | ✅ 4 mức màu, 4 mức nét, khử nhiễu nhẹ | Đã xem khung hình: màu da tự nhiên, lá bài rõ |
| Lá bài sắc nét | ✅ Ảnh gốc + bóng đổ mềm | **Đã sửa**: vị trí mặc định ban đầu che mặt người nói |
| Motion graphics | ✅ Remotion + HyperFrames | **Đã sửa**: lúc lật bài, mặt sau hiện thành mặt trước bị lật gương |
| Nhạc nền + tự hạ khi nói | ✅ Hạ 9–10 dB khi nói, 0 dB khi nghỉ; giọng nhỏ hơn 12 dB vẫn hạ 10 dB | **Đã sửa**: bản đầu chỉ hạ 1,3 dB |
| Âm lượng | ✅ −14,0 LUFS, đỉnh ≤ −1 dBTP | Chuẩn TikTok / Reels / Shorts |
| Xuất MP4 9:16 | ✅ 1080×1920, H.264 High, 30 fps cố định, yuv420p, AAC 48 kHz, faststart | Nối intro/outro mờ chuyển 0,3 s |
| Quy trình một lệnh `kvt dung` | ✅ 10,5 phút cho video 1 phút 46 s | Turbo trên CPU là bước chậm nhất |
| Kiểm thử tự động | ✅ 10/10 bài đạt | `tests/test_kvt.py` |

## 5. Chưa làm / hạn chế
- Chưa thử với video thật của Kendy (giọng Kendy, phòng quay của Kendy). Cần 1 video thô để tinh chỉnh ngưỡng, màu, cỡ chữ.
- Chưa xem trên điện thoại thật; mới xem khung hình trích xuất.
- Chưa có nhạc nền thật có bản quyền – Kendy cần cung cấp hoặc chọn trong thư viện TikTok/Instagram.
- Video quay ngang 1080p cắt sang dọc phải phóng to 1,78× → hình mềm hơn quay dọc. Khuyến nghị quay dọc.
- Máy không GPU: phụ đề turbo ~1,5× thời lượng video.
