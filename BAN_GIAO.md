# Bàn giao – dùng chung Kendy Video Toolkit giữa Claude và ChatGPT

Tài liệu cho mọi trợ lý AI tiếp nhận bộ công cụ. Đọc theo thứ tự: `CHECKPOINT.md` → tài liệu này → `SKILL.md`.

## 1. Ai làm được gì
| Môi trường | Chạy lệnh dựng video? | Làm được |
|---|---|---|
| Claude Code (máy tính hoặc phiên đám mây có kho này) | Có | Toàn bộ: cài, dựng, kiểm tra, hiệu chỉnh, commit khi Kendy cho phép |
| ChatGPT / Codex có môi trường chạy lệnh Linux, mạng, ≥ 8 GB RAM | Có | Như trên, theo `AGENTS.md` |
| ChatGPT phân tích dữ liệu (Code Interpreter) | Hạn chế | Thường không có mạng để cài gói; không dựng được trọn quy trình. Chỉ đọc cấu hình, soạn lời thoại / điểm nhấn |
| Claude / ChatGPT chỉ trò chuyện | Không | Tư vấn theo `SKILL.md`, soạn tệp cấu hình JSON và lời thoại để Kendy hoặc AI có máy chạy |
Không AI nào được giả vờ đã dựng video khi không chạy được lệnh.

## 2. Bắt đầu một phiên mới (AI có môi trường chạy lệnh)
```
git clone https://github.com/thanhthao3010kendy-dot/kendy-video-toolkit.git
cd kendy-video-toolkit
git checkout release/v1.0.0      # bản ổn định; phát triển tiếp trên main khi Kendy cho phép
./cai-dat.sh                     # ~4 phút, tự chạy 31 bài kiểm thử
```
Kho riêng tư: AI cần được Kendy cấp quyền đọc kho trên GitHub.

## 3. Ngôn ngữ chung giữa các AI
- **Một nguồn cấu hình**: mọi yêu cầu dựng được ghi thành tệp JSON theo mẫu `vi-du/*.json`, `"phong_cach": "kendy"`.
  AI chỉ trò chuyện soạn tệp này; AI có máy chạy `bin/kvt dung du-an.json`. Không trao đổi bằng mô tả miệng.
- **Một bộ quy tắc**: `CLAUDE.md` = `AGENTS.md` (cùng nội dung), `SKILL.md` là bộ định tuyến chọn lệnh.
- **Một nơi ghi tiến độ**: `CHECKPOINT.md` (trạng thái), `HIEU_CHINH.md` (kết quả hiệu chỉnh từng video).
  Kết thúc phiên: cập nhật hai tệp này và nói rõ việc đã làm / chưa làm.
- **Thời gian trong cấu hình** tính bằng giây trên video SAU khi cắt lặng (xem `lam-viec/03-cat-lang.mp4`).

## 4. Mẫu yêu cầu Kendy có thể gửi cho bất kỳ AI nào
> Dựng video `ten-video.mp4` theo phong cách Kendy. Lá bài: `mat-trang.jpg` hiện từ giây 6 đến 12.
> Điểm nhấn: «Lá bài chủ đạo – Mặt Trăng» giây 6–9. CTA cuối: «Theo dõi Kendy Huyền Học | Nhận thông điệp mỗi ngày».
> Lời thoại gốc: `loi-thoai.txt`. Từ điển: tarot. Không intro, không outro.

AI chuyển thành tệp JSON, chạy, gửi lại video + `*.bo-cuc.json` + `*.goi-y.json` + `*.doi-chieu.json` cho Kendy duyệt.

## 5. Điều không được làm
- Không sửa ứng dụng Bát Tự (kho `Kendy-tarot`) và Creative Studio.
- Không tự viết thông điệp Tarot / luận giải; chữ trên màn hình do Kendy cung cấp.
- Không tự áp dụng gợi ý từ điển; chỉ mục Kendy đánh dấu `"dong_y": true`.
- Không dùng dịch vụ trả phí, không `hyperframes publish/billing/templates`.
- Không đổi mặc định trong `presets/kendy.json` khi Kendy chưa duyệt. Không sửa nhánh `release/v1.0.0`.
- Không đưa video, mô hình, khoá API lên kho.

## 6. Báo cáo sau mỗi lần dựng (bắt buộc)
1. `bin/kvt kiem-tra RA.mp4` → `"dat": true` (1080×1920, 30 fps, −14 LUFS).
2. Ảnh 3 khung hình: đầu / giữa (lá bài, điểm nhấn) / cuối (CTA).
3. Các mục `"khong_che": false` trong `RA.bo-cuc.json`, gợi ý từ điển, khác biệt so với lời gốc.
4. Phần chưa kiểm (ví dụ chưa xem trên điện thoại thật).
