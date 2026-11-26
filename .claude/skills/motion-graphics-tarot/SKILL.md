---
name: motion-graphics-tarot
description: Tạo motion graphics vừa phải cho video Tarot dọc – intro lật lá bài, thẻ giới thiệu lá bài, outro thương hiệu – bằng Remotion (React) và HyperFrames (HTML+GSAP), dựng hoàn toàn trên máy. Dùng khi cần intro, outro, thẻ lá bài, tiêu đề động.
---

# Motion graphics Tarot

## Lệnh nhanh (tự tìm Chrome, tự chép ảnh, không cần nhớ đường dẫn)
```
bin/kvt intro   -o intro.mp4 --tieu-de "THÔNG ĐIỆP TAROT" --phu-de "Kendy Huyền Học" --anh la-bai.jpg
bin/kvt the-bai -o the.mp4 --anh la-bai.jpg --ten "Mặt Trăng (The Moon)" --y-nghia "<lời Kendy>"
bin/kvt outro   -o outro.mp4 --loi-moi "Theo dõi để nhận thông điệp tiếp theo" --ghi-chu "…"
bin/kvt xuat VAO.mp4 -o RA.mp4 --diem-nhan "Lá bài chủ đạo|Mặt Trăng@12-15" --cta "Theo dõi Kendy Huyền Học|…"
```
Bảng màu Kendy: xanh cổ vịt đậm #0B4F56, kem sáng #F6EFE0, vàng champagne #D8BE8C.
Motion graphics CHỈ ở nội dung quan trọng Kendy chỉ định (`diem_nhan`, `la_bai`, `cta`). Không tự thêm.
Intro / outro không bắt buộc.

## Remotion (`motion/remotion/`)
Bố cục: `TarotIntro` (3,5 s: lá bài bay lên, lật mặt, tiêu đề) và `LaBaiReveal` (4 s: ảnh lá bài + tên + ý nghĩa).
Ảnh và phông đặt trong `motion/remotion/public/`.
```
REMOTION_DISABLE_TELEMETRY=1 npx remotion render motion/remotion/src/index.jsx TarotIntro RA/intro.mp4 \
  --public-dir=motion/remotion/public --crf=16 \
  --browser-executable=<đường dẫn Chrome; bin/kvt intro tự tìm> \
  --props='{"tieuDe":"THÔNG ĐIỆP TAROT","phuDe":"Kendy Huyền Học","anhLaBai":"la-bai.jpg"}'
```
Giấy phép Remotion: miễn phí cho cá nhân / công ty ≤ 3 nhân viên. Nếu Kendy mở công ty > 3 người → cần mua
Company License. Nhắc Kendy khi điều kiện thay đổi.

## HyperFrames (`motion/hyperframes-outro/`)
`index.html` = outro 4 s (lá bài, "Kendy Huyền Học", lời mời theo dõi, ghi chú tham khảo). Chữ là biến
(`data-var-text`), GSAP lưu cục bộ ở `assets/gsap.min.js`.
```
cd motion/hyperframes-outro && npm run check && \
HYPERFRAMES_NO_TELEMETRY=1 ../../node_modules/.bin/hyperframes render -o ../../RA/outro.mp4 --quality delivery --no-browser-gpu
```
KHÔNG dùng: `hyperframes publish`, `billing`, `templates` (Pro), `reverse`, `auth login`, giọng/nhạc/ảnh do HeyGen tạo –
có thể phát sinh phí hoặc tải dữ liệu lên máy chủ HeyGen. Phải hỏi Kendy trước.

## Nguyên tắc "vừa phải"
- Mỗi chuyển động ≤ 1 s, dùng ease mềm (spring giảm chấn cao / power2–3). Không lắc, không nhấp nháy nhanh.
- Sao lấp lánh dùng hạt giống cố định → mỗi lần dựng giống hệt nhau.
- Phần chữ và lá bài nằm trong vùng an toàn: chừa 250 px trên, 450 px dưới cho giao diện TikTok/Reels.
- Ghép vào bài: `bin/kvt xuat ... --intro RA/intro.mp4 --outro RA/outro.mp4` (chuyển cảnh mờ 0,3 s).
