# Outro HyperFrames – Kendy

Bản mẫu outro 4 s (1080×1920) theo bảng màu Kendy. Dựng bằng `bin/kvt outro` ở thư mục gốc kho.
Đọc `../../.claude/skills/motion-graphics-tarot/SKILL.md` trước khi sửa.

- Chữ là biến (`data-composition-variables`): `thuongHieu`, `loiMoi`, `ghiChu`, `anhLaBai`.
- GSAP lưu cục bộ ở `assets/gsap.min.js`; phông ở `assets/fonts/`.
- KHÔNG dùng: `hyperframes publish`, `billing`, `templates`, `reverse`, `auth login`, media do HeyGen tạo,
  skill HyperFrames Pro – có thể phát sinh phí hoặc tải dữ liệu lên máy chủ ngoài. Phải hỏi Kendy trước.
- Kiểm tra: `npm run check`. Telemetry tắt bằng `HYPERFRAMES_NO_TELEMETRY=1`.
