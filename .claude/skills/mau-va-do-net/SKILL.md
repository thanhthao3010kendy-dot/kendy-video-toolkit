---
name: mau-va-do-net
description: Chỉnh màu, tăng độ nét, khử nhiễu và đưa video về khung dọc 9:16 (cắt theo người nói hoặc nền mờ) cho video Tarot – giữ màu da tự nhiên và lá bài sắc nét. Dùng khi cần chỉnh màu, làm nét, đổi khung ngang sang dọc.
---

# Màu, độ nét, khung 9:16

Tham số của `bin/kvt xuat` (hoặc mục `xuat` trong cấu hình):

## Khung (mặc định `--khung auto --tam-x auto`)
- auto: nguồn dọc → `vua`; nguồn ngang có mặt người → `cat` theo vị trí mặt (YuNet); không có mặt → `nen-mo`.
- `bin/kvt tim-mat VIDEO` để xem trước tâm mặt và khung gợi ý.
- `--khung cat --tam-x 0.5 [--zoom 1.0]`: cắt 9:16 quanh điểm ngang `tam-x` (0 trái → 1 phải). Video quay ngang:
  xem 1 khung hình, ước lượng vị trí mặt người nói (ví dụ 0,8). `--zoom` > 1 để cận hơn (giảm độ nét).
- `--khung nen-mo`: giữ nguyên toàn cảnh, nền là chính video làm mờ – hợp cảnh trải bài rộng.
- `--khung vua`: nguồn đã quay dọc.
- Video ngang 1080p cắt dọc phải phóng to ~1,78× → hình mềm hơn. Khuyên Kendy quay DỌC 1080×1920 hoặc 4K.

## Màu (`--mau`)
`tu-nhien` (mặc định, tương phản +4%, bão hoà +6%) · `huyen-bi` (tối hơi tím, sáng hơi ấm – hợp Tarot) ·
`kendy-tu-dong` (MẶC ĐỊNH phong cách Kendy từ v1.0.1: tự cân bằng trắng theo vùng gần trung tính – giảm ám vàng,
tự chỉnh độ sáng, hệ số giới hạn ±12% để giữ màu da; ghi số đo vào `*.bo-cuc.json` mục `chinh_mau`) ·
`sang` (cảnh thiếu sáng) · `kendy` (sáng, trong; tối ngả xanh cổ vịt, sáng ngả kem – rất nhẹ) · `khong`. Có thể dùng LUT riêng `--lut file.cube` (đặt trong `assets/luts/`).
Không đẩy bão hoà quá +10%: màu da và màu lá bài bị sai.

## Độ nét (`--net`)
`nhe` (mặc định, CAS 0,25) · `vua` (0,45) · `manh` · `khong`. Khử nhiễu nhẹ hqdn3d chạy TRƯỚC khi làm nét
(tắt bằng `--khong-khu-nhieu`). Làm nét quá tay → viền trắng quanh chữ trên lá bài, da sần.

## Lá bài sắc nét
`--la-bai anh.jpg@BAT_DAU-KET_THUC` (lặp được): chèn ảnh gốc độ phân giải cao, bóng đổ mềm, mờ vào/ra 0,35 s.
`--co-la-bai 0.36`, `--vi-tri-la-bai auto` (mặc định): tự chọn chỗ không che mặt (cấm tuyệt đối), tránh vùng tay cầm
bài và phụ đề; thiếu chỗ thì thu nhỏ, đặt lệch trái/phải. `--vien-la-bai "#D8BE8C"` viền champagne.
`--vung-tranh "x,y,rộng,cao@từ-đến"` khai báo thêm vùng không được che. Đọc `RA.bo-cuc.json`: mục `"khong_che": false`
cần xem lại khung hình. Ảnh lá bài: dùng ảnh Kendy chụp/scan hoặc bộ bài có quyền dùng (Rider-Waite-Smith 1909 là phạm vi công cộng).

## Phụ đề không che mặt / tay / lá bài
Mặc định phụ đề ở dưới. Dòng nào mà vị trí dưới chạm mặt (hoặc vùng `vung_tranh`), hoặc đè vùng nhiều chi tiết
(mặt lá bài sặc sỡ) trong khi chỗ khác trống hơn rõ rệt → tự chuyển lên "trên bàn" hoặc "trên". Giữ chỗ cũ nếu
vẫn ổn để không nhảy liên tục. Kết quả: `phu_de_doi_cho` trong `*.bo-cuc.json`. Tắt: `--phu-de-co-dinh`.

## Xem trước
Luôn trích 2–3 khung hình (`ffmpeg -ss T -i RA.mp4 -frames:v 1 x.png`) và xem trước khi báo xong.
