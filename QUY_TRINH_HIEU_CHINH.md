# Quy trình dựng & hiệu chỉnh bằng video quay thật

Mục tiêu: chỉnh thông số cho đúng phòng quay, giọng nói, cách cầm bài của Kendy, rồi đưa vào `presets/kendy.json`
(sau khi Kendy duyệt). Không thêm tính năng mới; chỉ đổi thông số đã có.

## A. Kendy chuẩn bị (mỗi lần một video)
1. Video thô quay **dọc**, nguyên bản từ điện thoại (không qua ứng dụng nén), 30–120 giây, đúng phòng và ánh sáng thường dùng.
2. Ảnh chụp / scan các lá bài xuất hiện trong video (càng nét càng tốt).
3. Lời thoại gốc dạng văn bản (nếu có).
4. Mốc thời gian muốn hiện lá bài / điểm nhấn (ước lượng theo video gốc cũng được) và câu CTA.
5. (Tuỳ chọn) tệp micro rời nếu có; nhạc nền có bản quyền.
Gửi trong cuộc trò chuyện hoặc qua đường dẫn Google Drive. Video **không** đưa lên kho mã.

## B. AI chạy lần đầu (không đổi mặc định)
```
bin/kvt probe video.mp4            # độ phân giải, fps, xoay, âm thanh
bin/kvt tim-mat video.mp4          # vị trí mặt, khung gợi ý
bin/kvt cat-lang video.mp4 -o lam-viec/cat.mp4 --chi-xem    # xem trước phần bị cắt
bin/kvt dung du-an.json            # phong cách kendy, dựng trọn
```

## C. Bảng hiệu chỉnh – xem gì, chỉnh gì
| Hạng mục | Cách xem | Thông số chỉnh (đã có sẵn) | Đạt khi |
|---|---|---|---|
| Cắt khoảng lặng | Nghe 3 điểm cắt bất kỳ; đọc `*.cat-lang.json` | `cat_lang_tham_so`: `lang_toi_thieu` 0,5–0,9; `dem` 0,15–0,3; `chuyen_mo` 0–0,15; `nguong` | Không cụt chữ đầu/cuối câu, không còn ngập ngừng dài, bỏ ≤ 40% |
| Âm thanh | Nghe tai nghe + loa điện thoại | `lam_sach_giong`; `muc_nhac_dB` −20…−26 | Giọng ấm, không rè, nhạc không lấn; `kiem-tra` −14 ± 1 LUFS |
| Phụ đề | Đọc SRT, `*.goi-y.json`, `*.doi-chieu.json` | `phu_de_tham_so`: `linh_vuc`, `ky_tu_toi_da` 24–32, `giay_toi_da`; `loi_goc` | Đúng chính tả thuật ngữ, ≤ 2 dòng, đọc kịp |
| Màu & sáng | So 3 khung hình với video gốc | `xuat.mau` (kendy / tu-nhien / sang), `xuat.lut` | Da tự nhiên, lá bài đúng màu, nền không bệt |
| Độ nét lá bài | Phóng to khung hình có lá bài | `xuat.net` nhe / vua / manh; `khu_nhieu`; ảnh `la_bai` | Chữ trên lá bài đọc được, không viền trắng |
| Bố cục | Đọc `*.bo-cuc.json`, xem khung hình | `vung_tranh` (vùng Kendy hay cầm bài), `co_la_bai`, `vi_tri_la_bai` | Không mục nào che mặt / lá bài; `khong_che` đều true |
| Khung hình | Xem đầu / giữa / cuối | `xuat.khung`, `tam_x`, `zoom` | Mặt và tay cầm bài trọn trong khung, không cắt đầu |
| Chuyển cảnh | Xem lướt toàn bài | `chuyen_canh`, `cat_lang_tham_so.chuyen_mo` | Mượt, không giật ở điểm cắt |

Mỗi lần chỉ đổi **một nhóm** thông số, dựng lại, so sánh trước / sau bằng ảnh khung hình cùng thời điểm.
Để thử nhanh: `"xuat": {"preset": "veryfast"}` và phụ đề `"mo_hinh": "small"`; bản cuối dùng mặc định.

## D. Ghi kết quả vào `HIEU_CHINH.md` (mẫu)
```
## Video 1 – <tên tệp>, <ngày>
- Nguồn: dọc 1080×1920, 30 fps, 74 s, phòng quay A, đèn …
- Thông số đã thử: … → kết quả …
- Đề xuất cập nhật presets/kendy.json: … (CHỜ KENDY DUYỆT)
- Còn tồn tại: …
```

## E. Chốt
1. Kendy duyệt bảng đề xuất.
2. Cập nhật `presets/kendy.json` (chỉ các mục đã duyệt), chạy 31 bài kiểm thử, dựng lại video mẫu.
3. Ghi `CHECKPOINT.md`; khi Kendy cho phép: commit lên `main`, phát hành v1.0.1.
