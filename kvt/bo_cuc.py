"""Bố cục an toàn: tìm khuôn mặt, quy đổi toạ độ sang khung 9:16, chọn vị trí không che mặt / lá bài / phụ đề.

Nhận diện mặt dùng YuNet (OpenCV, giấy phép MIT, 230 KB, chạy CPU). Không gửi hình đi đâu."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YUNET = ROOT / "assets" / "models" / "face_detection_yunet_2023mar.onnx"
OUT_W, OUT_H = 1080, 1920

# Vùng an toàn cho TikTok / Reels / Shorts (px trên khung 1080×1920)
SAFE_TOP = 230        # thanh "Following | For You"
SAFE_BOTTOM = 420     # mô tả, tên tài khoản, thanh nhạc
SAFE_RIGHT = 150      # cột nút thích / bình luận / chia sẻ
SAFE_LEFT = 60
SUB_BAND = (OUT_H - SAFE_BOTTOM - 210, OUT_H - SAFE_BOTTOM + 10)  # dải phụ đề 2 dòng


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    def grow(self, k: float) -> "Box":
        dx, dy = self.w * k, self.h * k
        return Box(self.x - dx, self.y - dy, self.w + 2 * dx, self.h + 2 * dy)

    def hits(self, o: "Box") -> bool:
        return not (self.x + self.w <= o.x or o.x + o.w <= self.x or self.y + self.h <= o.y or o.y + o.h <= self.y)

    def area_with(self, o: "Box") -> float:
        ix = max(0.0, min(self.x + self.w, o.x + o.w) - max(self.x, o.x))
        iy = max(0.0, min(self.y + self.h, o.y + o.h) - max(self.y, o.y))
        return ix * iy


@dataclass
class Geometry:
    """Ánh xạ toạ độ nguồn (đã xoay đúng chiều) → khung xuất 1080×1920."""
    scale: float
    off_x: float
    off_y: float

    def map(self, b: Box) -> Box:
        return Box(b.x * self.scale + self.off_x, b.y * self.scale + self.off_y, b.w * self.scale, b.h * self.scale)


def geometry(khung: str, w: int, h: int, crop: tuple[int, int, int, int] | None) -> Geometry:
    if khung == "cat" and crop:
        cw, ch, x, y = crop
        s = OUT_W / cw
        return Geometry(s, -x * s, -y * s)
    if khung == "nen-mo":
        s = min(OUT_W / w, OUT_H / h)
        return Geometry(s, (OUT_W - w * s) / 2, (OUT_H - h * s) / 2)
    s = max(OUT_W / w, OUT_H / h)  # 'vua'
    return Geometry(s, (OUT_W - w * s) / 2, (OUT_H - h * s) / 2)


def detect_faces(src: str, w: int, h: int, every: float = 0.5, max_frames: int = 400,
                 min_score: float = 0.75) -> list[tuple[float, list[Box]]]:
    """Trả [(thời điểm, [khung mặt theo toạ độ nguồn])]. FFmpeg tự xoay theo metadata điện thoại."""
    import numpy as np
    import cv2  # type: ignore

    if not YUNET.is_file():
        raise RuntimeError(f"Thiếu mô hình nhận diện mặt {YUNET.name} – chạy lại cai-dat.sh")
    aw = 640
    ah = int(round(h * aw / w / 2)) * 2
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", src, "-vf", f"fps={1 / every},scale={aw}:{ah}",
         "-frames:v", str(max_frames), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE)
    raw = proc.stdout
    size = aw * ah * 3
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (aw, ah), min_score)
    k = w / aw
    out = []
    for i in range(len(raw) // size):
        img = np.frombuffer(raw[i * size:(i + 1) * size], dtype=np.uint8).reshape(ah, aw, 3)
        _, faces = det.detect(img)
        boxes = []
        if faces is not None:
            for f in faces:
                boxes.append(Box(float(f[0]) * k, float(f[1]) * k, float(f[2]) * k, float(f[3]) * k))
        out.append((i * every, boxes))
    return out


def main_face_x(track: list[tuple[float, list[Box]]], w: int) -> float | None:
    """Tâm ngang trung vị của khuôn mặt lớn nhất (0..1) – để cắt khung 9:16 theo người nói."""
    xs = []
    for _, boxes in track:
        if boxes:
            b = max(boxes, key=lambda b: b.w * b.h)
            xs.append((b.x + b.w / 2) / w)
    if len(xs) < max(3, len(track) * 0.2):
        return None
    xs.sort()
    return xs[len(xs) // 2]


def hand_zone(face: Box) -> Box:
    """Vùng tay cầm lá bài ước lượng: ngay dưới mặt, rộng ~3,2 lần mặt, cao ~2,2 lần mặt.
    (Nhận diện trực tiếp lá bài trên tay không đủ tin cậy vì bị ngón tay che – nên tránh cả vùng.)"""
    return Box(face.x + face.w / 2 - 1.6 * face.w, face.y + face.h, 3.2 * face.w, 2.2 * face.h)


def obstacles_in(track_out: list[tuple[float, list[Box]]], s: float, e: float, hard_extra: list[Box],
                 soft_extra: list[Box] | None = None, tranh_tay: bool = True) -> tuple[list[Box], list[Box]]:
    """Trả (vùng CẤM, vùng NÊN TRÁNH). Cấm: mặt người nói, vùng Kendy khai báo, mục đã đặt.
    Nên tránh: vùng tay cầm lá bài ước lượng, dải phụ đề."""
    hard, soft = list(hard_extra), list(soft_extra or [])
    for t, boxes in track_out:
        if s - 0.5 <= t <= e + 0.5:
            hard += [b.grow(0.18) for b in boxes]   # chừa tóc, cằm, cử động nhẹ
            if tranh_tay:
                soft += [hand_zone(b) for b in boxes if b.w > 60]  # chỉ người nói (mặt đủ lớn)
    return hard, soft


def choose(cands: list[Box], hard: list[Box], soft: list[Box] | None = None) -> tuple[Box, bool]:
    """1) chỗ không chạm gì; 2) không chạm vùng cấm, chạm vùng nên tránh ít nhất; 3) chạm vùng cấm ít nhất.
    Trả (khung, True nếu hoàn toàn không che)."""
    soft = soft or []
    for c in cands:
        if not any(c.hits(o) for o in hard + soft):
            return c, True
    ok_hard = [c for c in cands if not any(c.hits(o) for o in hard)]
    if ok_hard:
        return min(ok_hard, key=lambda c: sum(c.area_with(o) for o in soft)), False
    return min(cands, key=lambda c: sum(c.area_with(o) for o in hard)), False


def card_candidates(card_w: float, card_h: float) -> list[Box]:
    """Vị trí lá bài thử lần lượt: giữa dưới cằm → trên cao → lệch trái/phải (nhỏ hơn)."""
    out = []
    usable_top, usable_bottom = SAFE_TOP, SUB_BAND[0] - 20
    for cy in (0.49, 0.40, 0.33):
        y = OUT_H * cy - card_h / 2
        if y >= usable_top and y + card_h <= usable_bottom:
            out.append(Box((OUT_W - card_w) / 2, y, card_w, card_h))
    for k in (0.8, 0.62):  # lệch trái / phải, nhỏ dần
        sw, sh = card_w * k, card_h * k
        for cy in (0.45, 0.33, 0.55):
            y = OUT_H * cy - sh / 2
            if y >= usable_top and y + sh <= usable_bottom:
                out.append(Box(SAFE_LEFT + 10, y, sw, sh))
                out.append(Box(OUT_W - SAFE_RIGHT - 10 - sw, y, sw, sh))
    return out


def banner_candidates(bw: float, bh: float, cta: bool = False) -> list[tuple[Box, bool]]:
    """Vị trí chữ điểm nhấn / CTA → [(khung, có_thay_chỗ_phụ_đề)].
    Thứ tự: trên cao → ngay trên phụ đề → thay chỗ phụ đề trong vài giây → giữa khung.
    CTA cuối video ưu tiên thay chỗ phụ đề sớm hơn (lời chào cuối không cần phụ đề)."""
    x = (OUT_W - bw) / 2
    top = (Box(x, SAFE_TOP + 20, bw, bh), False)
    above = (Box(x, SUB_BAND[0] - 30 - bh, bw, bh), False)
    band = (Box(x, SUB_BAND[1] - bh, bw, bh), True)
    mid = (Box(x, OUT_H * 0.42 - bh / 2, bw, bh), False)
    return [top, band, above, mid] if cta else [top, above, band, mid]


def subtitle_band() -> Box:
    return Box(SAFE_LEFT, SUB_BAND[0], OUT_W - SAFE_LEFT - SAFE_RIGHT, SUB_BAND[1] - SUB_BAND[0])
