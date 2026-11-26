# CHECKPOINT – Kendy Video Toolkit

Cập nhật: 26/11/2026 · Người cập nhật: Claude (Claude Code) · Chủ dự án: Kendy Huyền Học

## Trạng thái hiện tại
| Mục | Giá trị |
|---|---|
| Phiên bản ổn định | **v1.0.0** |
| Commit của v1.0.0 | `bc0b6a652263f9cf98955823ca5c4d66bb6737f0` |
| Kho | `github.com/thanhthao3010kendy-dot/kendy-video-toolkit` (riêng tư) |
| Nhánh | `main` (phát triển tiếp) · `release/v1.0.0` (cố định, không sửa) |
| Nhãn / Release `v1.0.0` | Đã công bố 26/11/2026 (không phải bản nháp / thử nghiệm); Claude xác minh nhãn trỏ đúng `bc0b6a6` |
| Kiểm thử | 31/31 đạt trên máy dựng và trên máy sạch tải từ GitHub (cài 3 phút 48 giây) |
| Giai đoạn | **v1.0.0 đã chốt, đóng băng tính năng.** Việc tiếp theo: hiệu chỉnh bằng video quay thật của Kendy |

## Đã có trong v1.0.0
- Lệnh `bin/kvt` (18 lệnh): cắt lặng, đồng bộ micro, lồng tiếng, ghép ảnh + video, phụ đề tiếng Việt (Whisper cục bộ),
  từ điển 6 lĩnh vực (chỉ gợi ý), đối chiếu lời gốc, khung 9:16 theo mặt, màu / nét, lá bài sắc nét, điểm nhấn, CTA,
  nhạc nền tự hạ, intro / thẻ lá bài (Remotion), outro (HyperFrames), kiểm tra, quy trình một lệnh.
- Phong cách Kendy `presets/kendy.json`: xanh cổ vịt đậm #0B4F56 · kem sáng #F6EFE0 · vàng champagne #D8BE8C.
- 9 skill: `SKILL.md` (định tuyến) + 8 skill chức năng trong `.claude/skills/`.
- Tài liệu: `README.md`, `CAI_DAT.md`, `PHIEN_BAN.md`, `BAO_CAO_KIEM_THU.md`, `BAN_GIAO.md`, `QUY_TRINH_HIEU_CHINH.md`,
  `AGENTS.md`, `CLAUDE.md`.

## Quy tắc cố định (không AI nào được tự thay đổi)
1. Không phát sinh chi phí khi Kendy chưa đồng ý.
2. Không tự sửa nội dung chuyên môn; từ điển ở trạng thái 【Chờ Kendy xác nhận cách viết】.
3. Không đụng ứng dụng Bát Tự (kho `Kendy-tarot`) và Creative Studio.
4. Không đưa video, mô hình, API key, dữ liệu cá nhân lên kho.
5. Commit / push / phát hành chỉ khi Kendy cho phép lần đó. Không sửa nhánh `release/v1.0.0`.
6. Đổi mặc định hình / tiếng (màu, vị trí, âm lượng) phải giải thích và chờ Kendy duyệt.

## Việc đang chờ
| # | Việc | Ai | Trạng thái |
|---|---|---|---|
| 1 | Xác minh nhãn / Release v1.0.0 trên GitHub trỏ `bc0b6a6` | Claude | ✅ Xong 26/11/2026 |
| 2 | Gửi 1–2 video quay thật + ảnh lá bài + lời thoại gốc | Kendy | Chờ |
| 3 | Hiệu chỉnh theo `QUY_TRINH_HIEU_CHINH.md`, ghi kết quả vào `HIEU_CHINH.md` | AI | Chưa bắt đầu |
| 4 | Kendy duyệt thông số hiệu chỉnh → cập nhật `presets/kendy.json` (bản v1.0.x) | Kendy duyệt | Chưa bắt đầu |
| 5 | Kendy xác nhận cách viết thuật ngữ trong `tu-dien/` | Kendy | Chưa bắt đầu |
| 6 | Nhạc nền có bản quyền | Kendy | Chưa có |

## Hạn chế đã biết (chi tiết: `BAO_CAO_KIEM_THU.md` mục 8)
- Phụ đề có thể đè lá bài khi hạ lá bài ngang dải phụ đề → sẽ khai báo `vung_tranh` theo khung hình thật.
- Chưa nhận diện trực tiếp lá bài trên tay (dùng vùng tay ước lượng).
- Video ngang cắt dọc mềm hơn quay dọc. Máy không GPU: phụ đề ~1,5× thời lượng video.
