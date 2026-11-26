---
name: cat-khoang-lang
description: Cắt khoảng lặng / chỗ ngập ngừng khỏi video nói chuyện Tarot mà vẫn tự nhiên (giữ đệm hơi thở, khớp khung hình, chống tiếng "tách"). Dùng khi cần rút gọn video thô, bỏ đoạn im lặng.
---

# Cắt khoảng lặng

```
bin/kvt cat-lang VAO.mp4 -o RA.mp4 [--chi-xem] [--che-do am-luong|loi-noi] [--nguong auto|-40]
                 [--lang-toi-thieu 0.55] [--dem 0.18] [--chuyen-mo 0.1]
```
- `--che-do auto` (mặc định): đo âm lượng trước; nếu gần như không có khoảng lặng (nhạc nền liên tục) thì tự chuyển sang `loi-noi`.
- Đầu vào có thể là video hoặc TỆP ÂM THANH (lồng tiếng .wav/.mp3) → ra .wav.
- Giữ động tác: khoảng lặng mà hình đang có chuyển động rõ (lật / xào / đặt bài) KHÔNG bị cắt (ngưỡng tự tính
  theo video, bỏ qua hiệu ứng lấp lánh nền). Tắt bằng `--khong-giu-dong-tac`. Báo cáo: `dong_tac_giu_lai` trong `*.cat-lang.json`.
- Không có Whisper: chế độ `auto` tự dùng `am-luong`.
- `--chuyen-mo 0.1`: mờ chồng 0,1 s ở mỗi điểm cắt cho bớt giật hình (phong cách Kendy dùng 0,1). 0 = cắt thẳng.

- `am-luong` (mặc định, nhanh): tự đo nền ồn và mức giọng của chính video để đặt ngưỡng
  (nền + 40% khoảng cách tới giọng). Có bước nâng đoạn nói nhỏ nên câu nói khẽ không bị cắt mất.
- `loi-noi`: dùng Whisper tìm khoảng trống giữa các từ. Dùng khi video có NHẠC NỀN liên tục
  (cách dò âm lượng sẽ không cắt được). Chậm hơn nhưng tạo luôn `RA.words.json` để làm phụ đề
  mà không phải nhận dạng lại (`phu-de --tu-json RA.words.json`).
- `--dem`: thời gian giữ thêm hai đầu câu. 0,15–0,25 s nghe tự nhiên; < 0,1 s nghe gấp, cụt hơi.
- `--lang-toi-thieu`: chỉ cắt khoảng lặng dài hơn mức này. Nói chậm, nhấn nhá: 0,7–0,9.
- Ranh giới cắt được làm tròn theo khung hình; mỗi điểm cắt có vi chỉnh âm 10 ms → không lệch tiếng, không "tách".
- Luôn chạy `--chi-xem` trước để xem số đoạn và số giây bị bỏ; nếu bỏ > 40% thời lượng, báo Kendy.
- Đầu ra trung gian chất lượng rất cao (CRF 12) để không mất nét ở bước sau.
- Báo cáo `RA.cat-lang.json` liệt kê các đoạn được giữ (mốc trên video gốc).
