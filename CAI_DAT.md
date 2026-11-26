# Cài đặt lại trên máy mới

## 1. Cài công cụ hệ thống (một lần)
- **Ubuntu / Debian**: `sudo apt install ffmpeg python3 python3-venv git curl` và Node.js 22 (nodejs.org hoặc `nvm install 22`).
- **macOS** (Homebrew): `brew install ffmpeg python@3.12 node@22 git`.
- **Windows**: dùng WSL2 (Ubuntu) rồi làm như Ubuntu.
Không cần GPU. RAM ≥ 8 GB (mô hình Whisper turbo dùng ~3 GB). Ổ đĩa trống ≥ 6 GB.

## 2. Lấy kho và cài
```
git clone https://github.com/<tài-khoản>/kendy-video-toolkit.git
cd kendy-video-toolkit
git checkout v1.0.0        # đúng bản ổn định
./cai-dat.sh               # 5–15 phút; cuối cùng tự chạy kiểm thử
```
Máy chậm mạng: `KVT_BO_QUA_MO_HINH=1 ./cai-dat.sh` (mô hình Whisper tự tải lần đầu dùng).

## 3. Thử
```
bin/kvt --help
bin/kvt kiem-tra video.mp4
```

## Ghi chú
- Mọi thứ cài trong thư mục kho (`.venv`, `node_modules`, `.cache`) – xoá thư mục là gỡ sạch.
- Chrome: tự tìm (biến `KVT_CHROME`, Playwright, google-chrome, chromium). Không có thì Remotion/HyperFrames tự tải bản headless miễn phí.
- yt-dlp: YouTube có thể chặn máy chủ đám mây; trên máy cá nhân thường tải được. Chỉ tải video có quyền sử dụng.
