# Báo cáo kiểm thử – kendy-video-toolkit v1.0.0 (26/11/2026)

Môi trường thử: máy ảo đám mây Linux, 4 lõi CPU, 15 GB RAM, **không GPU**.
Chưa thử trên máy của Kendy, chưa thử với video quay thật của Kendy, chưa xem trên điện thoại thật.

## 1. Công cụ, giấy phép, phần cứng
| Công cụ | Phiên bản | Giấy phép | Hoạt động | Ghi chú |
|---|---|---|---|---|
| FFmpeg | 6.1.1 | LGPL/GPL | ✅ | cắt, màu, nét, phụ đề, âm thanh, mã hoá |
| Whisper (CPU) | 20250625 | MIT | ✅ | tiếng Việt: turbo sai ~8% số từ, small ~42% |
| OpenCV YuNet | 5.0.0.93 / 2023mar | Apache-2.0 / MIT | ✅ | nhận diện mặt để bố cục |
| yt-dlp | 2026.10.26 | Unlicense | ⚠️ | archive.org được; YouTube chặn máy chủ đám mây |
| Remotion | 4.0.542 | miễn phí cá nhân / ≤ 3 người | ✅ | intro, thẻ lá bài |
| HyperFrames | 0.9.27 | Apache-2.0 | ✅ | outro, dựng cục bộ; lệnh có phí bị khoá |
Không phát sinh chi phí. Telemetry Remotion/HyperFrames đã tắt.

## 2. Dữ liệu thử thật
- Video Tarot tiếng Anh 1080p có người đọc bài cầm lá bài, có nhạc nền (archive.org, Public Domain Mark) – chỉ thử, không phát hành.
- Giọng đọc tiếng Việt thật Google FLEURS `vi_vn` (CC-BY 4.0), 10 câu, có lời gốc để đối chiếu.
- Ảnh lá bài The Moon, Rider-Waite-Smith 1909 (phạm vi công cộng). Nhạc nền thử: âm tổng hợp.

## 3. Kết quả chức năng
| Chức năng | Kết quả |
|---|---|
| Cắt khoảng lặng (tự chọn chế độ) | Giữ đủ 10/10 câu, kể cả câu nói rất nhỏ; hình–tiếng lệch < 1 ms; chuyển mờ 0,1 s ở điểm cắt |
| Đồng bộ micro rời | Tìm đúng +437 ms / −1250 ms; ghép xong đo lại 0 ms |
| Lồng tiếng WAV/MP3, ghép ảnh + video | ✅ thời lượng ảnh tự chia theo lời; ảnh đứng > 15 s có cảnh báo |
| Phụ đề tiếng Việt | turbo sai 7,8–8,5% số từ (có cả tên riêng nước ngoài) |
| Đối chiếu lời gốc | Báo 18 chỗ khác (8,6%); phụ đề mới dùng đúng nguyên văn lời gốc, mốc thời gian theo Whisper |
| Từ điển 6 lĩnh vực | 78 lá Tarot, 64 quẻ, 160 mục Manh Phái theo cách viết của ứng dụng Bát Tự; chỉ gợi ý, không tự sửa |
| Bố cục tránh mặt / lá bài | Mặt là vùng cấm; tránh vùng tay cầm bài; ảnh lá bài không bị phụ đề/CTA đè; CTA/điểm nhấn thay chỗ phụ đề khi cần |
| Phong cách Kendy | Màu `kendy`, phụ đề kem viền xanh cổ vịt, nhấn champagne, viền lá bài champagne |
| Nhạc nền tự hạ | Hạ 9–10 dB khi nói, 0 dB khi nghỉ; giọng nhỏ vẫn hạ đủ |
| Xuất | 1080×1920, H.264 High, 30 fps cố định, AAC 48 kHz, −14 LUFS ± 0,6 |
| Quy trình 1 lệnh | Video 2 phút 17 giây → 7,5 phút; ảnh + video + lồng tiếng 2 phút 17 giây → 6,8 phút (preset veryfast) |

## 4. Lỗi phát hiện khi thử và đã sửa
1. Cắt mất 2 câu nói nhỏ (ngưỡng cố định) → ngưỡng tự tính theo từng video.
2. Nhạc nền chỉ hạ 1,3 dB → chuẩn hoá tín hiệu điều khiển, hạ 9–10 dB.
3. Lật lá bài trong intro hiện mặt trước bị lật gương → chọn mặt theo góc xoay.
4. Lá bài chèn che mặt → nhận diện mặt, đặt tránh.
5. Khung chữ điểm nhấn / CTA che lá bài trên tay, rồi che mặt khi quay cận → vùng cấm (mặt) / vùng nên tránh (tay, phụ đề).
6. Phụ đề và CTA đè lên ảnh lá bài trong cảnh ảnh → ảnh đặt trong vùng an toàn, tự ghi vùng tránh.
7. Từ điển gợi ý nhầm từ thường ("năm diễn" → "Năm Tiền") → chỉ xét cặp âm hay nghe lẫn (s/x, tr/ch, d/gi/r/v, l/n, n/ng…).
8. Kịch bản cài báo nhầm "FFmpeg thiếu libass" trên máy sạch → sửa cách kiểm tra.

## 5. Kiểm thử tự động
31 bài (`tests/`): hàm lõi, cắt lặng, đồng bộ, xuất, từ điển, đối chiếu, bố cục, ghép cảnh, motion, tài liệu,
không có đường dẫn cố định của máy ảo. Kết quả trên máy dựng: **31/31 đạt**.

## 6. Kiểm tra khôi phục (môi trường sạch)
- Lần 1 – sao chép kho sang thư mục mới, thư mục người dùng riêng, không bộ nhớ đệm pip/npm: phát hiện lỗi số 8; sau khi sửa:
  cài trong 4 phút 10 giây (gồm tải ~2 GB mô hình), **28/28 bài đạt** (bản trước khi thêm 3 bài cuối).
- Lần 2 – tải từ GitHub về máy sạch: đạt, xem mục 7.

## 7. Khôi phục từ GitHub
Tải kho `thanhthao3010kendy-dot/kendy-video-toolkit` (commit 69f7199) về thư mục mới, thư mục người dùng riêng,
không bộ nhớ đệm pip/npm/mô hình → `./cai-dat.sh`: cài trong **3 phút 48 giây** (gồm tải ~2 GB mô hình Whisper),
tự tìm Chrome headless, **31/31 bài kiểm thử đạt**. Không phụ thuộc đường dẫn cố định của máy ảo (có bài kiểm thử riêng).

## 8. Hạn chế còn lại
- Phụ đề có thể đè lá bài khi người nói hạ lá bài xuống ngang dải phụ đề – cần hiệu chỉnh theo khung hình thật của Kendy
  (khai báo `vung_tranh` cố định trong phong cách).
- Nhận diện trực tiếp lá bài trên tay chưa đủ tin cậy (bị ngón tay che) – dùng vùng tay ước lượng thay thế.
- Video quay ngang cắt dọc bị phóng 1,78× → mềm hơn quay dọc. Khuyến nghị quay dọc 1080×1920 hoặc 4K.
- Máy không GPU: phụ đề turbo ~1,5× thời lượng video.
- Chưa thử trường hợp máy hoàn toàn không có Chrome (Remotion sẽ tự tải bản headless miễn phí).
