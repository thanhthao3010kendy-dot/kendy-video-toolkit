#!/usr/bin/env bash
# Cài bộ công cụ dựng video Kendy trên máy mới (độc lập, không đụng hệ thống khác, không phát sinh chi phí).
# Cần sẵn: FFmpeg ≥ 6 (libx264 + libass), Python ≥ 3.10, Node.js ≥ 22, git. Chrome/Chromium: có thì dùng, không có
# thì Remotion/HyperFrames tự tải bản headless miễn phí khi dựng lần đầu.
# Tuỳ chọn: KVT_BO_QUA_MO_HINH=1 bỏ tải mô hình Whisper (~2 GB) – tải sau khi dùng lần đầu.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
say() { printf '\n== %s\n' "$*"; }

say "Kiểm tra công cụ hệ thống"
for b in ffmpeg ffprobe python3 node npm; do command -v $b >/dev/null || { echo "Thiếu $b – cài trước (xem CAI_DAT.md)"; exit 1; }; done
# đọc hết danh sách trước rồi mới tìm (tránh lỗi "ống bị đóng sớm" khi dùng pipefail)
FILTERS="$(ffmpeg -hide_banner -filters 2>/dev/null)"; ENCODERS="$(ffmpeg -hide_banner -encoders 2>/dev/null)"
grep -q " subtitles " <<<"$FILTERS" || { echo "FFmpeg thiếu libass (phụ đề)"; exit 1; }
grep -q "libx264" <<<"$ENCODERS" || { echo "FFmpeg thiếu libx264"; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || { echo "Cần Python ≥ 3.10"; exit 1; }
node -e 'process.exit(parseInt(process.versions.node) >= 22 ? 0 : 1)' || { echo "Cần Node.js ≥ 22"; exit 1; }

say "Môi trường Python riêng (.venv)"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q --index-url https://download.pytorch.org/whl/cpu torch==2.15.0
.venv/bin/pip install -q -r requirements.txt -c requirements.lock

say "Gói Node (Remotion, HyperFrames) theo package-lock.json"
npm ci --no-audit --no-fund
HYPERFRAMES_NO_TELEMETRY=1 node_modules/.bin/hyperframes telemetry disable >/dev/null 2>&1 || true

say "Mô hình nhận diện mặt YuNet (MIT, 230 KB)"
M=assets/models/face_detection_yunet_2023mar.onnx
SHA=8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
mkdir -p assets/models
if [ ! -f "$M" ] || ! echo "$SHA  $M" | sha256sum -c --quiet 2>/dev/null; then
  curl -fsSL -o "$M" https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx
  echo "$SHA  $M" | sha256sum -c --quiet || { echo "Tệp mô hình YuNet sai mã kiểm tra"; rm -f "$M"; exit 1; }
fi

say "Trình duyệt headless cho motion graphics"
.venv/bin/python -c "import sys; sys.path.insert(0,'kvt'); import motion; print(motion.find_chrome() or 'Không thấy – Remotion sẽ tự tải khi dựng lần đầu')"

if [ "${KVT_BO_QUA_MO_HINH:-0}" != "1" ]; then
  say "Mô hình Whisper (turbo ~1,5 GB, small ~0,46 GB) → .cache/whisper"
  XDG_CACHE_HOME="$DIR/.cache" .venv/bin/python -c "import whisper; [whisper.load_model(m, device='cpu', download_root='.cache/whisper') for m in ('small','turbo')]"
fi

say "Chạy kiểm thử"
.venv/bin/python -m unittest discover -s tests
echo; echo "Cài đặt xong. Bắt đầu: bin/kvt --help   |   đọc SKILL.md"
