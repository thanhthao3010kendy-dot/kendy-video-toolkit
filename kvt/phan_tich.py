"""Phân tích hình ảnh nhẹ (chỉ numpy + FFmpeg, không cần mạng, không cần OpenCV):

- mẫu khung hình nhỏ để phân tích nhanh (lưu đệm .npz để chạy lại không phải giải mã lại)
- cân bằng trắng & độ sáng tự động (giảm ám vàng, giữ màu da)
- đường chuyển động theo thời gian (không cắt nhầm lúc lật / xào bài)
- độ "nhiều chi tiết" của từng vùng (lá bài sặc sỡ, nhiều cạnh) để phụ đề tránh
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import numpy as np

OUT_W, OUT_H = 1080, 1920


def _key(src: str, extra: str) -> str:
    p = Path(src)
    st = p.stat()
    return hashlib.sha1(f"{p.resolve()}|{st.st_size}|{int(st.st_mtime)}|{extra}".encode()).hexdigest()[:16]


def sample(src: str, fps: float = 4.0, width: int = 160, cache_dir: Path | None = None, max_frames: int = 2400):
    """Trả (frames uint8 [N,H,W,3] RGB, fps). Đệm trong cache_dir nếu có."""
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        f = cache_dir / f"mau-{_key(src, f'{fps}-{width}')}.npz"
        if f.is_file():
            d = np.load(f)
            return d["frames"], float(d["fps"])
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:"
                            "stream_side_data=rotation", "-of", "csv=p=0", src], stdout=subprocess.PIPE, text=True)
    nums = [int(float(x)) for x in probe.stdout.replace("\n", ",").split(",") if x.strip().lstrip("-").replace(".", "").isdigit()]
    w, h = nums[0], nums[1]
    if len(nums) > 2 and abs(nums[2]) % 180 == 90:
        w, h = h, w
    hh = int(round(h * width / w / 2)) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", src, "-vf", f"fps={fps},scale={width}:{hh}",
                          "-frames:v", str(max_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE).stdout
    n = len(raw) // (width * hh * 3)
    frames = np.frombuffer(raw[: n * width * hh * 3], dtype=np.uint8).reshape(n, hh, width, 3)
    if cache_dir:
        np.savez_compressed(f, frames=frames, fps=fps)
    return frames, fps


# ---------------------------------------------------------------- màu & sáng


def color_correction(frames: np.ndarray, strength: float = 0.75, max_gain: float = 0.12) -> dict:
    """Cân bằng trắng theo vùng gần trung tính (tường, hoa trắng, giấy) + độ sáng theo trung vị độ chói.

    Chỉ dùng điểm ảnh gần trung tính (bão hoà thấp, không quá tối/sáng) nên da và lá bài sặc sỡ
    không kéo lệch phép đo; hệ số giới hạn ±12% để màu da vẫn tự nhiên."""
    x = frames.reshape(-1, 3).astype(np.float32) / 255.0
    if len(x) > 400_000:
        x = x[:: len(x) // 400_000 + 1]
    mx, mn = x.max(1), x.min(1)
    sat = (mx - mn) / (mx + 1e-6)
    luma = x @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    neutral = (sat < 0.30) & (luma > 0.25) & (luma < 0.92)
    used = int(neutral.sum())
    gains = np.ones(3, dtype=np.float32)
    if used > 500:
        m = x[neutral].mean(0)
        target = m.mean()
        gains = 1 + strength * (target / (m + 1e-6) - 1)
        gains = np.clip(gains, 1 - max_gain, 1 + max_gain)
        gains /= gains @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)  # giữ độ sáng chung
    med = float(np.median(luma))
    # gamma đưa trung vị về ~0,46, giới hạn để không bệt / không cháy
    gamma = float(np.clip(np.log(0.46) / np.log(max(med, 1e-3)), 0.88, 1.12)) if 0.05 < med < 0.95 else 1.0
    cast = {"r": float(gains[0]), "g": float(gains[1]), "b": float(gains[2])}
    return {"he_so_mau": cast, "gamma": round(gamma, 3), "do_choi_trung_vi": round(med, 3),
            "diem_trung_tinh": used, "ty_le_trung_tinh": round(used / max(1, len(x)), 3)}


def correction_filter(c: dict) -> str:
    g = c["he_so_mau"]
    parts = []
    if any(abs(v - 1) > 0.01 for v in g.values()):
        parts.append(f"colorchannelmixer=rr={g['r']:.4f}:gg={g['g']:.4f}:bb={g['b']:.4f}")
    if abs(c["gamma"] - 1) > 0.02:
        # eq gamma > 1 làm sáng vùng tối-trung; đảo theo định nghĩa: out = in^(1/gamma)
        parts.append(f"eq=gamma={1 / c['gamma']:.3f}")
    return ",".join(parts)


def apply_numpy(img: np.ndarray, c: dict) -> np.ndarray:
    """Áp cùng phép chỉnh lên ảnh numpy (để xem trước nhanh / kiểm thử)."""
    g = c["he_so_mau"]
    x = img.astype(np.float32) / 255.0 * np.array([g["r"], g["g"], g["b"]], dtype=np.float32)
    x = np.clip(x, 0, 1) ** c["gamma"]
    return (x * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- chuyển động


def motion_profile(frames: np.ndarray, fps: float) -> tuple[np.ndarray, float]:
    """Độ chuyển động mỗi khung (0..1) và ngưỡng 'có động tác' tự tính.

    Hiệu ứng lấp lánh có sẵn trong video tạo nền chuyển động đều → ngưỡng = trung vị × 2,5 (tối thiểu 0,02)."""
    g = frames.astype(np.float32).mean(3) / 255.0
    if len(g) < 2:
        return np.zeros(len(g)), 1.0
    d = np.abs(np.diff(g, axis=0))
    # chỉ đếm điểm thay đổi rõ (> 8%) → nhiễu và lấp lánh nhỏ ít ảnh hưởng
    m = (d > 0.08).mean(axis=(1, 2))
    m = np.concatenate([[m[0]], m])
    thr = max(0.02, float(np.median(m)) * 2.5)
    return m, thr


def action_intervals(m: np.ndarray, thr: float, fps: float, min_len: float = 0.3, join: float = 0.4) -> list[tuple[float, float]]:
    """Các khoảng thời gian có động tác (lật / xào / đặt bài)."""
    on = m > thr
    out, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            out.append([i / fps, j / fps])
            i = j
        else:
            i += 1
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] <= join:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged if b - a >= min_len]


# ---------------------------------------------------------------- vùng nhiều chi tiết (lá bài)


def busy_map(frame: np.ndarray) -> np.ndarray:
    """Bản đồ 0..1: cao ở vùng sặc sỡ + nhiều cạnh (mặt lá bài), thấp ở nền tối / trơn (khăn bàn)."""
    x = frame.astype(np.float32) / 255.0
    mx, mn = x.max(2), x.min(2)
    sat = (mx - mn) / (mx + 1e-6) * (mx > 0.15)
    gray = x.mean(2)
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    edge = np.clip((gx + gy) * 6, 0, 1)
    return np.clip(0.6 * sat + 0.4 * edge, 0, 1)


def band_busy(frames: np.ndarray, fps: float, t0: float, t1: float, geo, band_out: tuple[float, float, float, float]) -> float:
    """Độ nhiều chi tiết trung bình của một vùng (toạ độ khung xuất 1080×1920) trong [t0, t1]."""
    i0, i1 = max(0, int(t0 * fps)), min(len(frames), int(np.ceil(t1 * fps)) + 1)
    if i1 <= i0:
        i0, i1 = max(0, min(len(frames) - 1, i0)), max(1, min(len(frames), i0 + 1))
    h, w = frames.shape[1:3]
    x, y, bw, bh = band_out
    # khung xuất → toạ độ nguồn (đơn vị ảnh mẫu): src = (out - off) / scale
    sx0 = (x - geo.off_x) / geo.scale
    sy0 = (y - geo.off_y) / geo.scale
    sx1 = (x + bw - geo.off_x) / geo.scale
    sy1 = (y + bh - geo.off_y) / geo.scale
    k = w / geo.src_w
    c0, c1 = int(max(0, sx0 * k)), int(min(w, sx1 * k))
    r0, r1 = int(max(0, sy0 * k)), int(min(h, sy1 * k))
    if c1 <= c0 or r1 <= r0:
        return 0.0
    vals = [busy_map(frames[i])[r0:r1, c0:c1].mean() for i in range(i0, i1, max(1, (i1 - i0) // 6))]
    return float(np.mean(vals)) if vals else 0.0
