---
name: dong-bo-loi-thoai
description: Đồng bộ lời thoại – ghép âm thanh micro rời (micro cài áo, máy ghi âm) vào video quay bằng điện thoại cho khớp môi, và khớp phụ đề theo từng từ. Dùng khi có tệp âm thanh riêng hoặc tiếng lệch hình.
---

# Đồng bộ lời thoại

## Micro rời → video
```
bin/kvt dong-bo VIDEO.mp4 MICRO.wav            # chỉ đo độ lệch
bin/kvt dong-bo VIDEO.mp4 MICRO.wav -o RA.mp4  # đo + thay âm thanh video bằng micro
```
- Thuật toán: tương quan chéo đường bao năng lượng 1 ms (bền với khác micro, khác âm lượng, có ồn).
  Độ chính xác ±1 ms. Hình không bị mã hoá lại (giữ nguyên chất lượng).
- Độ tin cậy < 1,3 → cảnh báo: hai bản ghi có thể không cùng cảnh. Phải nghe lại, không dùng mù quáng.
- Video và micro cần có cùng tiếng nói (camera có micro trong). Mẹo khi quay: vỗ tay một cái lúc bắt đầu.
- Kiểm chứng: chạy lại `dong-bo VIDEO RA.mp4` → phải ra 0 ms.

## Lồng tiếng thu sau (không cùng buổi quay)
`bin/kvt long-tieng VIDEO.mp4 LOI.mp3 -o RA.mp4` – thay hẳn âm thanh; hình kéo dài (giữ khung cuối) hoặc cắt cho khớp lời.
Với ảnh + lồng tiếng: `bin/kvt ghep-canh anh1.jpg video.mp4@0-5 anh2.png -o RA.mp4 --long-tieng LOI.wav`
(thời lượng ảnh tự chia theo độ dài lời; chuyển cảnh mờ 0,4 s).

## Phụ đề khớp lời
- Whisper cho mốc thời gian từng từ (`*.words.json`); phụ đề ASS tô màu đúng lúc từ được nói.
- Sau khi cắt lặng bằng `--che-do loi-noi`, mốc từ được chuyển sang dòng thời gian mới, không cần nhận dạng lại.
- Có lời gốc (văn bản Kendy viết): `bin/kvt doi-chieu RA.words.json loi-goc.txt -o RA-loi-goc` → phụ đề dùng ĐÚNG
  lời gốc, mốc thời gian lấy từ Whisper, kèm báo cáo chỗ nói khác lời gốc.
- Nếu Kendy sửa chữ trong SRT: `bin/kvt srt2ass SUA.srt -o SUA.ass` (giữ mốc câu, bỏ tô màu từng từ).
