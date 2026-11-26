# CHECKPOINT – Kendy Video Toolkit

Cập nhật: 26/11/2026 · Người cập nhật: Claude (Claude Code) · Chủ dự án: Kendy Huyền Học

## Trạng thái hiện tại
| Mục | Giá trị |
|---|---|
| Bản ổn định (dự phòng) | **v1.0.0** – nhánh `main` + `release/v1.0.0`, Release đã công bố, nhãn trỏ `bc0b6a6`. KHÔNG sửa |
| Bản đang thử | **v1.0.1-beta** – nhánh `phat-trien/v1.0.1`. CHƯA phát hành, CHƯA nghiệm thu bằng video thật |
| Kho | `github.com/thanhthao3010kendy-dot/kendy-video-toolkit` (riêng tư) |
| Kiểm thử tự động | 44/44 đạt (video tổng hợp, máy đầy đủ); 22/22 đạt ở chế độ nhẹ không mạng, không OpenCV |
| Giai đoạn | Đóng băng tính năng. Việc duy nhất: nghiệm thu v1.0.1-beta bằng video thật `1000037183.mp4` |

## v1.0.1-beta có thêm gì (so với v1.0.0)
| Chức năng | Trạng thái |
|---|---|
| `kvt moi-truong`: tự nhận diện thư viện có sẵn, bảng chức năng dùng được | Đã kiểm thử (máy đầy đủ + python3 trần) |
| Chế độ không mạng `KVT_NGOAI_TUYEN=1` | Đã kiểm thử |
| Cài nhẹ `./cai-dat.sh --nhe` (dùng python3 sẵn có, không PyTorch/Whisper/Node) | Đã kiểm thử trên máy không mạng |
| YuNet đóng gói sẵn (MIT, 230 KB) → dự phòng Haar → bỏ qua | Đã kiểm thử YuNet và "bỏ qua"; Haar CHƯA thử trên OpenCV 4 |
| Phụ đề không Whisper: SRT có sẵn (`phu_de_sua`) | Đã kiểm thử |
| Phụ đề không Whisper: lời gốc → mốc ƯỚC LƯỢNG | Chỉ tạo bản nháp; mặc định KHÔNG ghép vào video (`phu_de_uoc_luong_cho_phep`) |
| `dung` chia công đoạn, điểm lưu `lam-viec/trang-thai.json`, `--gioi-han-giay` (mã 3 = chạy tiếp) | Đã kiểm thử |
| `xuat --chia-doan N` (xuất từng đoạn, ghép không mã hoá lại) | Đã kiểm thử: PSNR 46 dB so với xuất 1 lần, lệch tiếng 0 ms |
| Cắt lặng giữ lúc lật / xào / đặt bài (dò chuyển động) | Đã kiểm thử video tổng hợp; **CHƯA nghiệm thu video thật** |
| Màu `kendy-tu-dong` (tự cân bằng trắng, giảm ám vàng, ±12%) – mặc định phong cách `kendy` | Thử trên 1 khung hình thật của Kendy; **CHƯA nghiệm thu video thật, CHỜ KENDY DUYỆT** |
| Phong cách `kendy-mau-cu` (màu cũ v1.0.0) để so sánh | Có |
| Phụ đề tự đổi chỗ tránh mặt / vùng lá bài | Đã kiểm thử video tổng hợp; **CHƯA nghiệm thu video thật, CHỜ KENDY DUYỆT** |
| Sửa lỗi chuẩn âm lượng khi âm thanh im lặng hoàn toàn | Đã kiểm thử |

## Chưa nghiệm thu bằng video thật (bắt buộc trước khi phát hành v1.0.1)
1. Cắt lặng: không mất chữ, không cắt nhầm động tác lật bài.
2. Màu: giảm ám vàng tự nhiên, da tự nhiên – so `kendy` với `kendy-mau-cu`.
3. Lá bài sắc nét; phụ đề không che mặt / tay / lá bài; không đè chữ "Kendy huyền học" có sẵn trong video.
4. Đồng bộ hình – tiếng – phụ đề; nhạc nền không lấn giọng; xuất 1080×1920 xem được trên điện thoại.
5. Chạy trọn trong ChatGPT với `--gioi-han-giay` + `chia_doan`.
Ghi kết quả vào `HIEU_CHINH.md`. Chỉ khi Kendy duyệt mới: gộp vào `main`, phát hành v1.0.1.

## Quy tắc cố định (không AI nào được tự thay đổi)
1. Không phát sinh chi phí khi Kendy chưa đồng ý.
2. Không tự sửa lời thoại / nội dung chuyên môn; từ điển chỉ gợi ý, trạng thái 【Chờ Kendy xác nhận cách viết】.
3. Không ghép phụ đề có mốc ước lượng vào video khi Kendy chưa chấp nhận.
4. Không đụng ứng dụng Bát Tự (kho `Kendy-tarot`) và Creative Studio.
5. Không đưa video, mô hình Whisper, API key, dữ liệu cá nhân lên kho (YuNet 230 KB MIT là ngoại lệ đã duyệt).
6. Commit / push / phát hành chỉ khi Kendy cho phép lần đó. Không sửa `main`, `release/v1.0.0` khi chưa nghiệm thu.
7. Đổi mặc định hình / tiếng phải giải thích và chờ Kendy duyệt.

## Việc đang chờ
| # | Việc | Ai | Trạng thái |
|---|---|---|---|
| 1 | Nghiệm thu v1.0.1-beta bằng `1000037183.mp4` (ChatGPT đã có video; Claude chưa có) | ChatGPT / Claude | Chờ |
| 2 | Gửi `1000037183.mp4` cho Claude (Google Drive) để đối chiếu chéo | Kendy | Chờ |
| 3 | Duyệt màu `kendy-tu-dong` và phụ đề tự đổi chỗ | Kendy | Chờ |
| 4 | Lời thoại gốc + CTA của video thử | Kendy | Chờ |
| 5 | Xác nhận cách viết thuật ngữ trong `tu-dien/` · nhạc nền có bản quyền | Kendy | Chưa có |
