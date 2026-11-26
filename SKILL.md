---
name: kendy-video
description: Bộ định tuyến dựng video dọc 9:16 (1080×1920) cho Kendy Huyền Học (Tarot, Bát Tự Manh Phái, Tử Vi, Phong Thủy, Kinh Dịch, Nhân Tướng). Đọc đầu tiên khi có yêu cầu dựng / sửa / cắt / làm phụ đề / chỉnh màu / thêm nhạc / xuất video, hoặc khi nhận video quay thật, ảnh, lời thoại, file lồng tiếng WAV/MP3. Chọn đúng skill con và đúng lệnh kvt.
---

# Kendy Video – bộ định tuyến

Mọi lệnh chạy ở thư mục gốc kho `kendy-video-toolkit` bằng `bin/kvt <lệnh>`. Chạy trên máy, miễn phí.
Chưa cài: `./cai-dat.sh` (xem `CAI_DAT.md`).

## Bước 0a – Kiểm tra môi trường (mỗi phiên mới)
`bin/kvt moi-truong` (không mạng: `KVT_NGOAI_TUYEN=1 bin/kvt moi-truong --khong-thu-mang`) → bảng chức năng dùng được.
- Không có Whisper → phụ đề từ lời gốc (`loi_goc`, mốc ƯỚC LƯỢNG) hoặc SRT có sẵn (`phu_de_sua`).
- Không có OpenCV → không tránh mặt (vẫn tránh vùng lá bài). Không có Node → bỏ intro/outro.
- Giới hạn thời gian mỗi lần chạy (ChatGPT) → `bin/kvt --gioi-han-giay 50 dung du-an.json`, `"xuat": {"chia_doan": 8}`;
  mã thoát 3 = đã lưu điểm dừng, chạy lại ĐÚNG lệnh đó cho tới mã 0. Không cài lại môi trường giữa các lần.

## Bước 0 – Nhận diện đầu vào (tự động)
| Kendy đưa | Nhận biết | Lối đi |
|---|---|---|
| 1 video quay thật | .mp4 .mov .mkv .webm | `video` → quy trình đầy đủ |
| Video + micro rời cùng buổi quay | thêm .wav/.mp3 ghi cùng lúc | `dong-bo` (skill `dong-bo-loi-thoai`) |
| Video + file lồng tiếng thu sau | .wav/.mp3 không trùng buổi quay | `long-tieng` (thay tiếng) |
| Ảnh (lá bài, minh hoạ) + lồng tiếng | .jpg .png .webp + .wav/.mp3 | `ghep-canh` / cấu hình `canh` |
| Lời thoại gốc (văn bản) | .txt | `doi-chieu` – phụ đề theo đúng lời gốc |
| Chỉ âm thanh cần cắt lặng | .wav .mp3 | `cat-lang` ra .wav |
Không chắc → `bin/kvt probe TỆP` và `bin/kvt tim-mat VIDEO`.

## Bước 1 – Chọn skill theo yêu cầu
| Yêu cầu của Kendy | Skill | Lệnh chính |
|---|---|---|
| "Dựng hoàn chỉnh", "làm video đăng TikTok/Reels" | `dung-video-tarot` | `bin/kvt dung du-an.json` (phong cách `kendy`) |
| Bỏ khoảng lặng, ngập ngừng, rút gọn | `cat-khoang-lang` | `cat-lang` |
| Ghép micro / lồng tiếng, tiếng lệch hình, khớp phụ đề | `dong-bo-loi-thoai` | `dong-bo`, `long-tieng`, `doi-chieu` |
| Phụ đề, sửa chính tả thuật ngữ, đối chiếu lời gốc | `phu-de-tieng-viet` | `phu-de --linh-vuc`, `tu-dien`, `sua-phu-de`, `doi-chieu` |
| Màu, sáng, nét, khung dọc, lá bài rõ | `mau-va-do-net` | `xuat --mau kendy --net vua --khung auto` |
| Intro, thẻ lá bài, outro, chữ điểm nhấn, CTA | `motion-graphics-tarot` | `intro`, `the-bai`, `outro`, `xuat --diem-nhan --cta` |
| Nhạc nền, khử ồn, âm lượng | `am-thanh-nhac-nen` | `am-thanh` |
| Xuất file, kiểm tra trước khi đăng | `xuat-video-doc` | `xuat`, `kiem-tra` |
Một chức năng riêng lẻ → gọi đúng lệnh đó. Nhiều chức năng → `dung` với tệp cấu hình.

## Bước 2 – Tự chọn công cụ (mặc định `auto`, chỉ ghi đè khi Kendy yêu cầu)
- Cắt lặng: `--che-do auto` → đo âm lượng; nếu gần như không có khoảng lặng (có nhạc nền) → dùng Whisper.
- Khung: `--khung auto` → nguồn dọc giữ nguyên; nguồn ngang có mặt → cắt theo mặt; không mặt → nền mờ.
- Bố cục: lá bài / chữ / CTA tự đặt, KHÔNG che mặt (cấm tuyệt đối), tránh vùng tay cầm bài và phụ đề;
  không còn chỗ → chữ thay chỗ phụ đề vài giây. Kết quả ghi ở `*.bo-cuc.json` (xem cảnh báo).
- Motion: Remotion cho intro / thẻ lá bài (React); HyperFrames cho outro / CTA thương hiệu (HTML).
  Ghép chữ điểm nhấn trực tiếp bằng FFmpeg (nhẹ, nhanh) khi chỉ cần một dòng chữ.
- Phụ đề: Whisper `turbo` (chính xác) cho bản đăng; `small` chỉ để xem nhanh; không có Whisper → lời gốc / SRT.
- Cắt lặng giữ lại lúc tay lật / xào / đặt bài (dò chuyển động); phụ đề tự lên trên khi vị trí dưới đè mặt / lá bài.
- Màu `kendy-tu-dong`: tự cân bằng trắng (giảm ám vàng) và độ sáng theo từng video, giữ màu da.

## Quy tắc bắt buộc
1. Không phát sinh chi phí: không `hyperframes publish/billing/templates/reverse/auth`, không API trả phí.
2. Không tự sửa nội dung chuyên môn. Từ điển chỉ GỢI Ý chính tả; chỉ áp dụng mục Kendy đánh dấu `"dong_y": true`.
   Thuật ngữ đánh dấu 【Chờ Kendy xác nhận】 giữ nguyên trạng thái.
3. Chữ trên màn hình (điểm nhấn, CTA, tên lá bài, ý nghĩa) do Kendy cung cấp; không tự viết thông điệp Tarot.
4. Không đụng kho `Kendy-tarot`, ứng dụng Bát Tự, Creative Studio.
5. Không đưa video nguồn, mô hình, API key lên kho mã.
6. Trước khi báo xong: `bin/kvt kiem-tra RA.mp4` đạt + xem 3 khung hình (đầu / giữa / cuối) + đọc `*.bo-cuc.json`.
   Nói rõ phần chưa kiểm (ví dụ chưa xem trên điện thoại thật).
