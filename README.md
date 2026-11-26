# kendy-video-toolkit – Bộ công cụ dựng video dọc cho Kendy Huyền Học

Dựng video dọc 9:16 (1080 × 1920) cho Tarot, Bát Tự Manh Phái, Tử Vi, Phong Thủy, Kinh Dịch, Nhân Tướng.
Chạy hoàn toàn trên máy, **không phát sinh chi phí**. Độc lập: không liên quan và không sửa ứng dụng Bát Tự
(kho `Kendy-tarot`) hay Creative Studio.

- Cài đặt: [`CAI_DAT.md`](CAI_DAT.md) · Phiên bản thư viện: [`PHIEN_BAN.md`](PHIEN_BAN.md)
- Cho AI: [`SKILL.md`](SKILL.md) (định tuyến) · [`AGENTS.md`](AGENTS.md) · [`CLAUDE.md`](CLAUDE.md) · `.claude/skills/`
- Kết quả kiểm thử: [`BAO_CAO_KIEM_THU.md`](BAO_CAO_KIEM_THU.md)
- Trạng thái & bàn giao: [`CHECKPOINT.md`](CHECKPOINT.md) · [`BAN_GIAO.md`](BAN_GIAO.md) (Claude / ChatGPT) · [`QUY_TRINH_HIEU_CHINH.md`](QUY_TRINH_HIEU_CHINH.md)

## Làm được gì
| Chức năng | Lệnh |
|---|---|
| Toàn bộ quy trình theo cấu hình (phong cách Kendy) | `bin/kvt dung du-an.json` |
| Cắt khoảng lặng (video hoặc file lồng tiếng), chuyển mờ ở điểm cắt | `bin/kvt cat-lang` |
| Ghép micro rời cùng buổi quay / thay bằng lồng tiếng WAV-MP3 | `bin/kvt dong-bo` · `bin/kvt long-tieng` |
| Ghép video + ảnh lá bài + lồng tiếng | `bin/kvt ghep-canh` |
| Phụ đề tiếng Việt (Whisper cục bộ), tô màu từ đang nói | `bin/kvt phu-de --linh-vuc tarot` |
| Gợi ý sửa thuật ngữ (không tự sửa) · áp dụng mục Kendy đồng ý | `bin/kvt tu-dien` · `bin/kvt sua-phu-de` |
| Đối chiếu phụ đề với lời thoại gốc, phụ đề theo lời gốc | `bin/kvt doi-chieu` |
| Khung 9:16 tự động theo khuôn mặt | `bin/kvt tim-mat` · `xuat --khung auto` |
| Màu, độ nét, lá bài sắc nét, chữ điểm nhấn, CTA – không che mặt / lá bài | `bin/kvt xuat` |
| Nhạc nền tự hạ khi nói, −14 LUFS | `bin/kvt am-thanh` |
| Intro lật lá bài, thẻ lá bài (Remotion), outro (HyperFrames) | `bin/kvt intro` · `the-bai` · `outro` |
| Kiểm tra tệp trước khi đăng | `bin/kvt kiem-tra` |

Mọi lệnh có `--help`. Mẫu cấu hình: `vi-du/du-an-mau.json` (video thật), `vi-du/anh-va-long-tieng.json`,
`vi-du/video-long-tieng.json`. Phong cách riêng: `presets/kendy.json`.

## Phong cách Kendy (`"phong_cach": "kendy"`)
Xanh cổ vịt đậm `#0B4F56` · kem sáng `#F6EFE0` · vàng champagne `#D8BE8C`. Hình sáng, sắc (màu `kendy`, nét `vua`),
lá bài viền champagne; cắt lặng có mờ chồng 0,1 s; nối cảnh mờ 0,4 s; phụ đề kem viền xanh, từ đang nói chuyển champagne;
motion graphics chỉ ở điểm nhấn Kendy chỉ định; intro/outro tắt mặc định; CTA cuối video tuỳ chỉnh.

## Thành phần
FFmpeg · Whisper (openai-whisper, CPU) · OpenCV YuNet (nhận diện mặt) · yt-dlp · Remotion · HyperFrames · GSAP.
Chi tiết phiên bản và giấy phép: `PHIEN_BAN.md`.

## Không phát sinh chi phí – KHÔNG dùng khi chưa được Kendy đồng ý
`hyperframes publish | billing | templates | reverse | auth login`, media do HeyGen tạo, API AI trả phí.
Telemetry đã tắt (`HYPERFRAMES_NO_TELEMETRY=1`, `REMOTION_DISABLE_TELEMETRY=1`).

## Bản quyền nội dung
- yt-dlp chỉ dùng cho video của Kendy hoặc có giấy phép tái sử dụng.
- Ảnh lá bài: ảnh Kendy chụp, hoặc Rider-Waite-Smith 1909 (phạm vi công cộng). Bộ bài hiện đại thường có bản quyền.
- Nhạc nền: nhạc Kendy sở hữu / có giấy phép rõ, hoặc chọn trong thư viện TikTok/Instagram khi đăng.

## Kiểm thử
```
.venv/bin/python -m unittest discover -s tests -v       # 25 bài
KVT_BO_QUA_MOTION=1 .venv/bin/python -m unittest discover -s tests   # bỏ phần dựng Remotion/HyperFrames
```
