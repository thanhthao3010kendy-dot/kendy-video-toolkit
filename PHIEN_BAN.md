# Danh sách phiên bản – kendy-video-toolkit v1.0.0

Tất cả miễn phí. Phiên bản được ghim (chọn bản đã phát hành ≥ 2 tuần lúc cài để tránh lỗi bản mới).

## Hệ thống (cài bằng trình quản lý gói của máy)
| Thành phần | Đã kiểm thử | Tối thiểu | Giấy phép |
|---|---|---|---|
| FFmpeg / FFprobe | 6.1.1 (Ubuntu 24.04) | 6.0, có libx264, libass | LGPL / GPL |
| Python | 3.13.18 | 3.10 | PSF |
| Node.js | 22.23.5 | 22 | MIT |
| Chrome / Chromium headless | Chrome for Testing 158 | bất kỳ bản mới | BSD (tự tải nếu thiếu) |

## Python (`requirements.txt`, đầy đủ: `requirements.lock`)
| Gói | Phiên bản | Giấy phép |
|---|---|---|
| openai-whisper | 20250625 | MIT |
| torch (CPU) | 2.15.0 | BSD-3 |
| yt-dlp | 2026.10.26 | Unlicense |
| opencv-python-headless | 5.0.0.93 | Apache-2.0 |
| numpy | 2.5.5 | BSD |

## Node (`package.json`, khoá: `package-lock.json`)
| Gói | Phiên bản | Giấy phép |
|---|---|---|
| remotion, @remotion/cli, @remotion/renderer, @remotion/bundler | 4.0.542 | Remotion License – miễn phí cho cá nhân / tổ chức ≤ 3 người |
| hyperframes | 0.9.27 | Apache-2.0 |
| react, react-dom | 18.3.1 | MIT |

## Tài nguyên đi kèm kho
| Tài nguyên | Nguồn | Giấy phép |
|---|---|---|
| Be Vietnam Pro (Medium, Bold), Cormorant Garamond SemiBold | Google Fonts | SIL OFL 1.1 |
| GSAP 3.15.0 (`motion/hyperframes-outro/assets/gsap.min.js`) | gsap.com | GSAP Standard "no charge" |
| Ảnh mẫu The Moon (Rider-Waite-Smith 1909) | Wikimedia Commons | Phạm vi công cộng |

| YuNet face_detection_yunet_2023mar.onnx (từ v1.0.1, `assets/models/`) | OpenCV Zoo | MIT (`LICENSE-YuNet.txt`), 230 KB |

## Chế độ nhẹ (v1.0.1, ChatGPT): chỉ cần FFmpeg + python3 + numpy; OpenCV tuỳ chọn (có thì tránh mặt)

## Tải khi cài (không lưu trong kho)
| Tài nguyên | Dung lượng | Giấy phép | Kiểm tra |
|---|---|---|---|
| Whisper turbo (large-v3-turbo), small | 1,5 GB + 0,46 GB | MIT | mã băm của openai-whisper |
