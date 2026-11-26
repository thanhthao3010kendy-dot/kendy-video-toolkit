---
name: am-thanh-nhac-nen
description: Xử lý âm thanh tự nhiên cho video Tarot – làm sạch giọng nói, nhạc nền tự hạ khi nói (ducking), chuẩn âm lượng −14 LUFS cho TikTok/Reels/Shorts. Dùng khi cần thêm nhạc nền, khử ồn, cân âm lượng.
---

# Âm thanh & nhạc nền

```
bin/kvt am-thanh VAO.mp4 -o RA.wav [--nhac nhac.mp3] [--muc-nhac -22] [--khong-ha-nhac] [--khong-lam-sach] [--lufs -14]
```
(`bin/kvt xuat` tự gọi bước này với cùng tham số.)

## Chuỗi xử lý giọng (nhẹ tay để giữ chất giọng)
lọc dưới 75 Hz (tiếng ù) → lọc trên 15,5 kHz → khử ồn FFT nhẹ (8 dB) → giảm âm xì → nén 2,2:1 → chuẩn hoá 2 lượt
EBU R128: −14 LUFS, đỉnh thật −1,5 dBTP.

## Lồng tiếng
Tệp lồng tiếng WAV/MP3/M4A dùng chung chuỗi làm sạch & chuẩn hoá. Cắt lặng tệp âm thanh: `bin/kvt cat-lang LOI.mp3 -o LOI-cat.wav`.

## Nhạc nền
- Nhạc tự lặp cho đủ dài, mờ vào 1,5 s, mờ ra 2,5 s cuối.
- `--muc-nhac`: −20 đến −24 dB là vừa (mặc định −20; Tarot thì thầm nên dùng −22 đến −24).
- Tự hạ nhạc ~9–10 dB khi Kendy nói (sidechain ngưỡng 0,05, tỉ lệ 4:1, nhả 400 ms; tín hiệu điều khiển được chuẩn hoá nên giọng nhỏ vẫn hạ đủ) – nhạc dâng lại ở khoảng nghỉ. Đã đo bằng `tests/duck_test.py`.
- BẢN QUYỀN: chỉ dùng nhạc Kendy sở hữu, nhạc miễn phí bản quyền có giấy phép rõ (ghi nguồn), hoặc chọn nhạc
  trong thư viện của TikTok/Instagram khi đăng. Không lấy nhạc từ YouTube bằng yt-dlp để đăng lại.
- Nhạc thử trong `test-media/nhac_thu.wav` là âm tổng hợp chỉ để kiểm thử, không dùng phát hành.

## Kiểm tra
`bin/kvt kiem-tra RA.mp4` → âm lượng phải −14 ± 1,5 LUFS, đỉnh ≤ −1 dB.
