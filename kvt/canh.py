"""Ghép cảnh: video quay thật + hình ảnh + lời thoại / lồng tiếng (WAV, MP3, M4A…) → một video dọc 1080×1920.

- Ảnh (lá bài, ảnh minh hoạ): đặt TRỌN ảnh lên nền mờ của chính ảnh (không cắt mất góc lá bài),
  chuyển động phóng rất chậm (≤ 4%) để không tĩnh, có thể tắt.
- Video: tự cắt 9:16 theo khuôn mặt nếu quay ngang.
- Lồng tiếng: nếu có, thay âm thanh các cảnh; thời lượng ảnh tự chia theo độ dài lời thoại.
- Chuyển cảnh: mờ chồng (dissolve) 0,4 s – mượt, tự nhiên.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

OUT_W, OUT_H = 1080, 1920
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
AUD_EXT = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def kind_of(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMG_EXT:
        return "anh"
    if ext in AUD_EXT:
        return "am-thanh"
    return "video"


def image_clip(img: str, out: str, dur: float, fps: float, zoom: bool) -> None:
    frames = max(1, int(round(dur * fps)))
    # nền: chính ảnh phủ kín khung, làm mờ & tối nhẹ; tiền cảnh: trọn ảnh, cao tối đa 86% khung
    fg_h = int(OUT_H * 0.86)
    if zoom:
        # phóng 2× rồi zoompan → chuyển động mượt, không rung; tối đa +4% trong suốt cảnh
        z = f"zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={OUT_W}x{OUT_H}:fps={fps}"
    else:
        z = f"fps={fps}"
    graph = (
        f"[0:v]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H},boxblur=40:4,"
        f"eq=brightness=-0.10:saturation=0.85,setsar=1[bg];"
        f"[0:v]scale=-2:{fg_h}:flags=lanczos,scale='min(iw,{OUT_W - 120})':-2:flags=lanczos,setsar=1[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,scale={OUT_W * 2}:{OUT_H * 2}:flags=lanczos,{z},"
        f"scale={OUT_W}:{OUT_H}:flags=lanczos,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}",
                    "-i", img, "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", graph, "-map", "[v]", "-map", "1:a", "-frames:v", str(frames),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "aac", "-b:a", "256k",
                    "-r", str(fps), out], check=True)


def plan_durations(scenes: list[dict], voice_dur: float | None, probe_dur, xf: float) -> list[float]:
    """Thời lượng từng cảnh. Video: theo 'tu'/'den' hoặc cả tệp. Ảnh: 'giay' hoặc chia đều phần lời thoại còn lại."""
    durs: list[float | None] = []
    for s in scenes:
        if "video" in s:
            full = probe_dur(s["video"])
            a, b = float(s.get("tu", 0)), float(s.get("den", full))
            durs.append(max(0.5, min(b, full) - a))
        else:
            durs.append(float(s["giay"]) if s.get("giay") else None)
    free = [i for i, d in enumerate(durs) if d is None]
    if free:
        fixed = sum(d for d in durs if d is not None)
        target = voice_dur if voice_dur else fixed + 4.0 * len(free)
        each = (target + xf * (len(scenes) - 1) - fixed) / len(free)
        for i in free:
            durs[i] = max(2.0, each)
    return [float(d) for d in durs]
