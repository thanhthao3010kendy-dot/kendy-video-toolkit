#!/usr/bin/env python3
"""kvt – Kendy Video Toolkit: dựng video Tarot dọc 9:16 (1080×1920).

Bộ công cụ độc lập, chạy hoàn toàn trên máy (không gọi dịch vụ trả phí).
Dùng: FFmpeg/FFprobe, openai-whisper (cục bộ), OpenCV YuNet (nhận diện mặt), Remotion, HyperFrames.

Từng chức năng:
  probe        Xem thông số tệp           tim-mat     Nhận diện mặt, gợi ý khung 9:16
  cat-lang     Cắt khoảng lặng            dong-bo     Ghép micro rời / lồng tiếng cùng buổi quay
  long-tieng   Thay âm thanh bằng WAV/MP3 ghep-canh   Ghép video + ảnh + lồng tiếng
  phu-de       Phụ đề tiếng Việt (Whisper) srt2ass    SRT đã sửa → ASS
  tu-dien      Gợi ý sửa thuật ngữ (không tự sửa)     sua-phu-de  Áp dụng gợi ý Kendy đồng ý
  doi-chieu    Đối chiếu phụ đề với lời gốc, dựng phụ đề theo lời gốc
  am-thanh     Làm sạch giọng, nhạc nền tự hạ, −14 LUFS
  intro / the-bai / outro   Motion graphics (Remotion / HyperFrames)
  xuat         Khung 9:16, màu, nét, lá bài, điểm nhấn, CTA, phụ đề, intro/outro → MP4
  kiem-tra     Kiểm tra tệp xuất
Toàn bộ quy trình:
  dung         Chạy theo tệp cấu hình JSON (mẫu: vi-du/), phong cách riêng: "phong_cach": "kendy"
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bo_cuc  # noqa: E402
import canh  # noqa: E402
import motion  # noqa: E402
import tu_dien  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
LUTS_DIR = ROOT / "assets" / "luts"

OUT_W, OUT_H = 1080, 1920

# ---------------------------------------------------------------- tiện ích


class KvtError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[kvt] {msg}", file=sys.stderr, flush=True)


def need(binary: str) -> str:
    p = shutil.which(binary)
    if not p:
        raise KvtError(f"Không tìm thấy '{binary}'. Hãy cài đặt trước (xem README).")
    return p


def run(cmd: list[str], *, capture: bool = False, quiet: bool = True) -> subprocess.CompletedProcess:
    """Chạy lệnh; báo lỗi rõ ràng kèm 30 dòng cuối nếu thất bại."""
    if not quiet:
        log(" ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or "").strip().splitlines()[-30:])
        raise KvtError(f"Lệnh thất bại ({cmd[0]}):\n{tail}")
    return proc


def ffmpeg_base() -> list[str]:
    return [need("ffmpeg"), "-hide_banner", "-nostdin", "-y", "-loglevel", "error"]


def probe(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise KvtError(f"Không thấy tệp: {p}")
    out = run([need("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)]).stdout
    return json.loads(out)


def stream(info: dict, kind: str) -> dict | None:
    for s in info.get("streams", []):
        if s.get("codec_type") == kind and not s.get("disposition", {}).get("attached_pic"):
            return s
    return None


def duration_of(info: dict) -> float:
    d = info.get("format", {}).get("duration")
    if d is None:
        raise KvtError("Không đọc được thời lượng tệp.")
    return float(d)


def fps_of(info: dict) -> float:
    v = stream(info, "video")
    if not v:
        return 30.0
    for key in ("avg_frame_rate", "r_frame_rate"):
        num, _, den = (v.get(key) or "0/0").partition("/")
        try:
            f = float(num) / float(den or 1)
            if 1 <= f <= 240:
                return f
        except (ValueError, ZeroDivisionError):
            pass
    return 30.0


def display_size(v: dict) -> tuple[int, int]:
    """Kích thước hiển thị thật (tính cả xoay của điện thoại)."""
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(v.get("tags", {}).get("rotate", rot))
    if abs(rot) % 180 == 90:
        w, h = h, w
    return w, h


def fmt_ts(t: float, sep: str = ",") -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)) % 1000:03d}"


def ass_ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ffpath(p: str | Path) -> str:
    """Thoát ký tự cho đường dẫn dùng trong bộ lọc FFmpeg (subtitles=, lut3d=, movie=)."""
    s = str(Path(p).resolve())
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,").replace("[", "\\[").replace("]", "\\]")


# ---------------------------------------------------------------- 1. cắt khoảng lặng


@dataclass
class Seg:
    start: float
    end: float


def detect_silence_auto(src: str, noise_db: float | None, min_silence: float) -> tuple[list[Seg], float]:
    """Dò khoảng lặng theo năng lượng, ngưỡng tự tính theo từng video.

    dynaudnorm (chậm, ~8 s cửa sổ) nâng đoạn nói nhỏ lên để không bị coi là im lặng;
    ngưỡng = nền ồn + 40% khoảng cách tới mức giọng (tối thiểu +8 dB)."""
    import numpy as np
    sr, hop = 16000, 320  # khung 20 ms
    out = subprocess.run([need("ffmpeg"), "-v", "error", "-nostdin", "-i", src, "-vn", "-af",
                          "highpass=f=90,dynaudnorm=f=250:g=31:m=12", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         stdout=subprocess.PIPE)
    if out.returncode != 0 or not out.stdout:
        raise KvtError("FFmpeg không đọc được âm thanh để dò khoảng lặng.")
    x = np.frombuffer(out.stdout, dtype=np.float32)
    n = len(x) // hop
    if n < 5:
        raise KvtError("Âm thanh quá ngắn.")
    db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    if noise_db is None:
        live = db[db > -90] if (db > -90).sum() > n * 0.2 else db  # bỏ đoạn im tuyệt đối (số 0) khi tính nền
        floor, speech = np.percentile(live, 10), np.percentile(live, 95)
        noise_db = float(floor + max(8.0, 0.4 * (speech - floor)))
        log(f"Ngưỡng tự động: {noise_db:.1f} dB (nền {floor:.1f} dB, giọng {speech:.1f} dB)")
    quiet = db < noise_db
    sil: list[Seg] = []
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * hop / sr >= min_silence:
                sil.append(Seg(i * hop / sr, j * hop / sr if j < n else float("inf")))
            i = j
        else:
            i += 1
    return sil, noise_db


def silences_from_words(words: list[dict], total: float, min_silence: float) -> list[Seg]:
    """Khoảng lặng = khoảng trống giữa các từ Whisper nhận ra (bền với nhạc nền)."""
    sil, t = [], 0.0
    for w in sorted(words, key=lambda w: w["s"]):
        if w["s"] - t >= min_silence:
            sil.append(Seg(t, w["s"]))
        t = max(t, w["e"])
    if total - t >= min_silence:
        sil.append(Seg(t, float("inf")))
    return sil


def remap_words(segs_words: list[dict], keep: list[Seg], joins: list[float] | None = None) -> list[dict]:
    """Chuyển mốc thời gian lời nói sang dòng thời gian sau khi cắt (trừ phần chồng của chuyển cảnh mờ)."""
    offsets, acc = [], 0.0
    for i, k in enumerate(keep):
        if joins and i > 0:
            acc -= joins[i - 1]
        offsets.append((k.start, k.end, acc))
        acc += k.end - k.start

    def mp(t: float) -> float | None:
        for a, b, off in offsets:
            if a - 1e-3 <= t <= b + 1e-3:
                return round(off + min(max(t, a), b) - a, 3)
        return None

    out = []
    for seg in segs_words:
        words = []
        for w in seg["words"]:
            s, e = mp(w["s"]), mp(w["e"])
            if s is not None and e is not None and e >= s:
                words.append({**w, "s": s, "e": e})
        if words:
            out.append({"s": words[0]["s"], "e": words[-1]["e"], "text": " ".join(w["w"] for w in words),
                        "words": words})
    return out


def speech_segments(silences: list[Seg], total: float, pad: float, min_keep: float, fps: float) -> list[Seg]:
    keep: list[Seg] = []
    t = 0.0
    for s in silences:
        if s.start > t:
            keep.append(Seg(t, s.start))
        t = min(s.end, total)
    if t < total:
        keep.append(Seg(t, total))
    # đệm hai đầu cho tự nhiên (không cụt hơi)
    padded = [Seg(max(0.0, k.start - pad), min(total, k.end + pad)) for k in keep if k.end - k.start >= min_keep]
    merged: list[Seg] = []
    for k in padded:
        if merged and k.start <= merged[-1].end + 0.05:
            merged[-1].end = max(merged[-1].end, k.end)
        else:
            merged.append(Seg(k.start, k.end))
    # khớp ranh giới vào khung hình để hình – tiếng không lệch dần
    snapped = []
    for k in merged:
        a = math.floor(k.start * fps) / fps
        b = math.ceil(k.end * fps) / fps
        if b - a >= 1.0 / fps:
            snapped.append(Seg(round(a, 6), round(min(b, total), 6)))
    return snapped


def cmd_cat_lang(a: argparse.Namespace) -> dict:
    info = probe(a.input)
    total = duration_of(info)
    fps = fps_of(info)
    if not stream(info, "audio"):
        raise KvtError("Tệp không có âm thanh – không thể cắt khoảng lặng.")
    words = None
    threshold = None
    che_do = a.che_do
    if che_do == "auto":
        # dò theo âm lượng trước; gần như không có khoảng lặng trên video dài → nhiều khả năng có nhạc nền
        sil0, thr0 = detect_silence_auto(a.input, None, a.lang_toi_thieu)
        segs0 = speech_segments(sil0, total, a.dem, a.giu_toi_thieu, fps)
        kept0 = sum(x.end - x.start for x in segs0)
        che_do = "loi-noi" if (total > 20 and kept0 / total > 0.97) else "am-luong"
        log(f"Tự chọn chế độ cắt: {che_do} (theo âm lượng giữ {kept0 / total:.0%} thời lượng)")
    if che_do == "loi-noi":
        words = transcribe(a.input, a.mo_hinh, a.ngon_ngu, DEFAULT_PROMPT if a.ngon_ngu == "vi" else None)
        sil = silences_from_words([w for s in words for w in s["words"]], total, a.lang_toi_thieu)
    elif che_do == "am-luong":
        nguong = None if str(a.nguong).lower() == "auto" else float(a.nguong)
        sil, threshold = detect_silence_auto(a.input, nguong, a.lang_toi_thieu)
    else:
        raise KvtError("--che-do phải là: am-luong | loi-noi")
    segs = speech_segments(sil, total, a.dem, a.giu_toi_thieu, fps)
    if not segs:
        raise KvtError("Không tìm thấy đoạn có tiếng nói. Thử --nguong thấp hơn (ví dụ -50) hoặc --che-do loi-noi.")
    kept = sum(s.end - s.start for s in segs)
    log(f"Giữ {len(segs)} đoạn, {kept:.1f}s / {total:.1f}s (bỏ {total - kept:.1f}s khoảng lặng)")
    report = {"nguon": str(a.input), "che_do": che_do, "nguong_dB": threshold, "tong_giay": round(total, 3),
              "giu_giay": round(kept, 3), "doan": [{"bat_dau": s.start, "ket_thuc": s.end} for s in segs]}
    if a.chi_xem:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    has_video = stream(info, "video") is not None
    fade = min(0.012, 1.0 / fps / 2)  # vi chỉnh 10–12 ms chống tiếng "tách" ở điểm cắt
    xf = float(getattr(a, "chuyen_mo", 0) or 0)
    joins: list[float] = []
    if xf > 0 and len(segs) > 1:
        # chuyển cảnh mờ chồng rất ngắn giữa hai đoạn → bớt giật hình ở chỗ cắt (jump cut)
        for i in range(1, len(segs)):
            d = min(xf, (segs[i - 1].end - segs[i - 1].start) / 3, (segs[i].end - segs[i].start) / 3)
            joins.append(max(1, int(d * fps)) / fps)
    parts = []
    for i, s in enumerate(segs):
        d = s.end - s.start
        if has_video:
            parts.append(f"[0:v]trim=start={s.start:.6f}:end={s.end:.6f},setpts=PTS-STARTPTS,settb=AVTB[v{i}]")
        afx = "" if joins else f",afade=t=in:d={fade:.3f},afade=t=out:st={max(0.0, d - fade):.6f}:d={fade:.3f}"
        parts.append(f"[0:a]atrim=start={s.start:.6f}:end={s.end:.6f},asetpts=PTS-STARTPTS{afx}[a{i}]")
    if joins:
        vl, al, length = "v0", "a0", segs[0].end - segs[0].start
        for i in range(1, len(segs)):
            d = joins[i - 1]
            if has_video:
                parts.append(f"[{vl}][v{i}]xfade=transition=fade:duration={d:.6f}:offset={length - d:.6f}[vx{i}]")
                vl = f"vx{i}"
            parts.append(f"[{al}][a{i}]acrossfade=d={d:.6f}:c1=tri:c2=tri[ax{i}]")
            al = f"ax{i}"
            length += (segs[i].end - segs[i].start) - d
        if has_video:
            parts.append(f"[{vl}]null[vo]")
        parts.append(f"[{al}]anull[ao]")
        report["chuyen_mo_giay"] = joins
    else:
        labels = "".join((f"[v{i}]" if has_video else "") + f"[a{i}]" for i in range(len(segs)))
        parts.append(labels + f"concat=n={len(segs)}:v={1 if has_video else 0}:a=1" +
                     ("[vo][ao]" if has_video else "[ao]"))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(";\n".join(parts))
        script = fh.name
    try:
        cmd = ffmpeg_base() + ["-i", a.input, "-filter_complex_script", script]
        if has_video:
            # bản trung gian chất lượng rất cao để không mất nét qua các bước sau
            cmd += ["-map", "[vo]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                    "-pix_fmt", "yuv420p", "-fps_mode", "cfr", "-r", f"{fps:.6f}"]
        cmd += ["-map", "[ao]", "-c:a", "pcm_s16le" if a.output.endswith((".mov", ".mkv", ".wav")) else "aac",
                "-b:a", "320k", "-ar", "48000", a.output]
        run(cmd)
    finally:
        os.unlink(script)
    Path(a.output).with_suffix(".cat-lang.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    if words is not None:  # lời đã nhận dạng → chuyển sang dòng thời gian mới, khỏi nhận dạng lại
        wpath = Path(a.output).with_suffix(".words.json")
        wpath.write_text(json.dumps(remap_words(words, segs, joins), ensure_ascii=False, indent=1), "utf-8")
        report["tu_json"] = str(wpath)
    log(f"Đã xuất: {a.output}")
    return report


# ---------------------------------------------------------------- 2. đồng bộ micro rời


def _pcm(path: str, sr: int, seconds: float) -> "np.ndarray":
    import numpy as np
    out = subprocess.run([need("ffmpeg"), "-v", "error", "-nostdin", "-i", path, "-t", str(seconds), "-vn",
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], stdout=subprocess.PIPE)
    if out.returncode != 0 or not out.stdout:
        raise KvtError(f"Không đọc được âm thanh: {path}")
    return np.frombuffer(out.stdout, dtype=np.float32)


def find_offset(ref: str, other: str, seconds: float = 90.0, sr: int = 8000) -> tuple[float, float]:
    """Trả (độ lệch giây, độ tin cậy). Lệch > 0: 'other' bắt đầu muộn hơn 'ref' → cần cắt đầu 'other'."""
    import numpy as np
    x = _pcm(ref, sr, seconds)
    y = _pcm(other, sr, seconds)

    def env(sig):  # đường bao năng lượng 1 ms – bền với khác biệt micro
        hop = sr // 1000
        n = len(sig) // hop
        e = np.sqrt((sig[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
        e = np.log(e)
        e -= e.mean()
        return e / (e.std() + 1e-9)

    ex, ey = env(x), env(y)
    n = 1 << int(math.ceil(math.log2(len(ex) + len(ey))))
    corr = np.fft.irfft(np.fft.rfft(ey, n) * np.conj(np.fft.rfft(ex, n)), n)
    lag = int(np.argmax(corr))
    if lag > n // 2:
        lag -= n
    peak = corr.max()
    conf = float(peak / (np.sort(corr)[-200:-1].mean() + 1e-9)) if len(corr) > 400 else 0.0
    return lag / 1000.0, conf


def cmd_dong_bo(a: argparse.Namespace) -> dict:
    off, conf = find_offset(a.video, a.am_thanh, a.giay_phan_tich)
    log(f"Độ lệch micro rời so với video: {off * 1000:+.0f} ms (độ tin cậy {conf:.2f})")
    if conf < 1.3:
        log("CẢNH BÁO: độ tin cậy thấp – hai bản ghi có thể không cùng cảnh. Hãy kiểm tra bằng tai.")
    res = {"lech_giay": round(off, 3), "do_tin_cay": round(conf, 2)}
    if a.output:
        vinfo = probe(a.video)
        dur = duration_of(vinfo)
        if off >= 0:  # micro bắt đầu muộn hơn → micro lùi
            af = f"atrim=start={off:.3f},asetpts=PTS-STARTPTS"
        else:
            af = f"adelay={int(-off * 1000)}:all=1"
        run(ffmpeg_base() + ["-i", a.video, "-i", a.am_thanh, "-map", "0:v:0", "-map", "1:a:0",
                             "-af", af + f",apad,atrim=end={dur:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                             "-ar", "48000", "-t", f"{dur:.3f}", a.output])
        log(f"Đã ghép âm thanh micro vào video: {a.output}")
    print(json.dumps(res, ensure_ascii=False))
    return res


# ---------------------------------------------------------------- 3. phụ đề (Whisper)

# Câu "ảo giác" quen thuộc của Whisper khi gặp nhạc/khoảng lặng (tiếng Việt & Anh)
HALLUCINATIONS = [
    r"subscribe", r"đăng ký kênh", r"ghiền mì gõ", r"like.{0,20}share", r"bấm chuông",
    r"cảm ơn các bạn đã (theo dõi|xem)", r"thanks for watching", r"hẹn gặp lại các bạn trong (những )?video",
    r"phụ đề (bởi|được)", r"amara\.org", r"la la school",
]

DEFAULT_PROMPT = ("Kendy Huyền Học. Tarot, lá bài, Ẩn Chính, Ẩn Phụ, trải bài, thông điệp, "
                  "Cốc, Kiếm, Gậy, Tiền, The Moon, The Star, năng lượng.")


def is_hallucination(seg: dict) -> bool:
    text = seg.get("text", "").strip().lower()
    if not text:
        return True
    if any(re.search(p, text) for p in HALLUCINATIONS):
        return True
    if seg.get("no_speech_prob", 0) > 0.6 and seg.get("avg_logprob", 0) < -1.0:
        return True
    if seg.get("compression_ratio", 0) > 2.6:
        return True
    return False


def transcribe(src: str, model_name: str, language: str, prompt: str | None) -> list[dict]:
    import whisper  # type: ignore
    os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
    log(f"Đang tải mô hình Whisper '{model_name}' (lần đầu sẽ tải về máy, miễn phí)…")
    model = whisper.load_model(model_name, device="cpu", download_root=str(ROOT / ".cache" / "whisper"))
    log("Đang nhận dạng lời nói (CPU)…")
    res = model.transcribe(
        src, language=language, task="transcribe", fp16=False, word_timestamps=True,
        condition_on_previous_text=False, initial_prompt=prompt, temperature=(0.0, 0.2, 0.4),
        no_speech_threshold=0.6, compression_ratio_threshold=2.4, logprob_threshold=-1.0,
        hallucination_silence_threshold=1.0, verbose=None)
    segs = []
    dropped = 0
    for s in res["segments"]:
        if is_hallucination(s):
            dropped += 1
            continue
        words = [{"w": w["word"].strip(), "s": round(float(w["start"]), 3), "e": round(float(w["end"]), 3),
                  "p": round(float(w.get("probability", 1.0)), 3)}
                 for w in s.get("words", []) if w["word"].strip()]
        segs.append({"s": round(float(s["start"]), 3), "e": round(float(s["end"]), 3), "text": s["text"].strip(),
                     "words": words})
    if dropped:
        log(f"Đã loại {dropped} đoạn nghi là 'ảo giác' của Whisper (nhạc/khoảng lặng).")
    return segs


def chunk_words(segs: list[dict], max_chars: int, max_dur: float) -> list[dict]:
    """Chia lời thành các cụm ngắn dễ đọc trên màn hình dọc."""
    chunks = []
    for seg in segs:
        words = seg["words"] or [{"w": seg["text"], "s": seg["s"], "e": seg["e"], "p": 1}]
        cur: list[dict] = []
        for w in words:
            text_len = len(" ".join(x["w"] for x in cur + [w]))
            ends_sentence = bool(cur) and re.search(r"[.!?…]$", cur[-1]["w"])
            if cur and (text_len > max_chars or w["e"] - cur[0]["s"] > max_dur or ends_sentence):
                chunks.append(cur)
                cur = []
            cur.append(w)
        if cur:
            # không để một cụm mồ côi 1–2 từ: gộp vào cụm trước nếu không quá dài
            prev = chunks[-1] if chunks and chunks[-1][-1] in words else None
            if prev and len(cur) <= 2 and len(" ".join(x["w"] for x in prev + cur)) <= max_chars + 10 \
                    and cur[-1]["e"] - prev[0]["s"] <= max_dur + 1.5:
                prev.extend(cur)
            else:
                chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        start, end = c[0]["s"], c[-1]["e"]
        if i + 1 < len(chunks):  # giữ chữ trên màn hình tới cụm sau nếu khoảng trống ngắn
            nxt = chunks[i + 1][0]["s"]
            if nxt - end < 0.6:
                end = nxt
        out.append({"s": start, "e": max(end, start + 0.4), "words": c, "text": " ".join(w["w"] for w in c)})
    return out


def write_srt(chunks: list[dict], path: Path) -> None:
    lines = []
    for i, c in enumerate(chunks, 1):
        lines += [str(i), f"{fmt_ts(c['s'])} --> {fmt_ts(c['e'])}", c["text"], ""]
    path.write_text("\n".join(lines), "utf-8")


def parse_srt(path: Path) -> list[dict]:
    raw = path.read_text("utf-8-sig").replace("\r\n", "\n")
    out = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        rows = block.strip().split("\n")
        m = None
        for idx, row in enumerate(rows):
            m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", row)
            if m:
                text = " ".join(r.strip() for r in rows[idx + 1:] if r.strip())
                break
        if not m:
            continue
        g = list(map(int, m.groups()))
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        if e > s and text:
            out.append({"s": s, "e": e, "text": text, "words": []})
    return out


# Màu ASS viết dạng &HAABBGGRR (ngược thứ tự RGB)
KENDY = {"teal": "#0B4F56", "teal_dam": "#06333A", "kem": "#F6EFE0", "champagne": "#D8BE8C"}


def ass_color(hex_rgb: str, alpha: int = 0) -> str:
    h = hex_rgb.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


ASS_STYLES = {
    # tên: (phông, cỡ, màu chữ, màu nhấn (từ đang nói), màu viền, độ dày viền, bóng)
    "tarot": ("Be Vietnam Pro", 68, "&H00FFFFFF", "&H0060D8F5", "&H00201018", 4, 2),   # trắng, nhấn vàng kim
    "toi-gian": ("Be Vietnam Pro", 62, "&H00FFFFFF", "&H00FFFFFF", "&H00201018", 3, 1),
    # Kendy: chữ kem sáng, viền xanh cổ vịt đậm, từ đang nói chuyển vàng champagne
    "kendy": ("Be Vietnam Pro", 66, ass_color(KENDY["kem"]), ass_color(KENDY["champagne"]),
              ass_color(KENDY["teal_dam"]), 5, 1),
}
# Lề trái/phải chừa cột nút bên phải của TikTok/Reels
SUB_MARGIN_L, SUB_MARGIN_R = 110, 150


def ass_escape(t: str) -> str:
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def wrap_two_lines(words: list[str], max_line: int) -> str:
    text = " ".join(words)
    if len(text) <= max_line:
        return text
    best, best_score = None, 10 ** 9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = abs(len(a) - len(b))
        if score < best_score:
            best, best_score = (a, b), score
    return f"{best[0]}\\N{best[1]}" if best else text


def write_ass(chunks: list[dict], path: Path, style: str = "tarot", karaoke: bool = True,
              margin_v: int = 430, max_line: int = 22) -> None:
    font, size, primary, accent, outline_c, outline, shadow = ASS_STYLES.get(style, ASS_STYLES["tarot"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size},{primary},{accent},{outline_c},&H96000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,{SUB_MARGIN_L},{SUB_MARGIN_R},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = []
    for c in chunks:
        fade = r"{\fad(120,80)}"
        if karaoke and c["words"]:
            # đổi màu từng từ đúng lúc được nói – nhẹ nhàng, không nảy
            words, tokens = [w["w"] for w in c["words"]], []
            wrapped = wrap_two_lines(words, max_line)
            break_after = len(wrapped.split("\\N")[0].split(" ")) if "\\N" in wrapped else None
            for i, w in enumerate(c["words"]):
                nxt = c["words"][i + 1]["s"] if i + 1 < len(c["words"]) else c["e"]
                dur_cs = max(1, int(round((nxt - w["s"]) * 100)))
                lead = ""
                if i == 0 and w["s"] > c["s"]:
                    lead = r"{\k" + str(int(round((w["s"] - c["s"]) * 100))) + "}"
                sep = "\\N" if break_after and i == break_after else (" " if i else "")
                tokens.append(f"{sep}{lead}{{\\kf{dur_cs}}}{ass_escape(w['w'])}")
            # \kf tô dần màu Secondary→Primary; ta muốn chữ đã nói = màu nhấn → đảo vai trò màu trong dòng
            body = r"{\1c" + accent + r"&\2c" + primary + "&}" + "".join(tokens)
        else:
            body = wrap_two_lines([ass_escape(x) for x in c["text"].split()], max_line)
        rows.append(f"Dialogue: 0,{ass_ts(c['s'])},{ass_ts(c['e'])},Main,,0,0,0,,{fade}{body}")
    path.write_text(head + "\n".join(rows) + "\n", "utf-8")


def cmd_phu_de(a: argparse.Namespace) -> dict:
    out_dir = Path(a.thu_muc or Path(a.input).parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(a.input).stem
    linh_vuc = [x for x in (getattr(a, "linh_vuc", None) or "").split(",") if x.strip()]
    prompt = None if a.khong_goi_y else (a.goi_y or (DEFAULT_PROMPT if a.ngon_ngu == "vi" else None))
    if linh_vuc and not a.khong_goi_y:
        prompt = tu_dien.whisper_prompt(linh_vuc, a.goi_y or "Kendy Huyền Học.")
    if getattr(a, "tu_json", None):
        segs = json.loads(Path(a.tu_json).read_text("utf-8"))
        log(f"Dùng lời đã nhận dạng sẵn: {a.tu_json}")
    else:
        segs = transcribe(a.input, a.mo_hinh, a.ngon_ngu, prompt)
    (out_dir / f"{stem}.words.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), "utf-8")
    chunks = chunk_words(segs, a.ky_tu_toi_da, a.giay_toi_da)
    write_srt(chunks, out_dir / f"{stem}.srt")
    write_ass(chunks, out_dir / f"{stem}.ass", a.kieu, karaoke=not a.khong_nhan_tu)
    low = [w for s in segs for w in s["words"] if w["p"] < 0.4]
    log(f"Đã tạo {len(chunks)} dòng phụ đề → {out_dir}/{stem}.srt / .ass / .words.json")
    if linh_vuc:
        gy = tu_dien.suggest(segs, linh_vuc)
        (out_dir / f"{stem}.goi-y.json").write_text(json.dumps(gy, ensure_ascii=False, indent=1), "utf-8")
        log(f"Từ điển: {len(gy)} chỗ nghi sai thuật ngữ → {stem}.goi-y.json (chỉ gợi ý, CHƯA sửa; "
            "Kendy đánh dấu \"dong_y\": true rồi chạy 'kvt sua-phu-de')")
    if low:
        log(f"Có {len(low)} từ độ tin cậy thấp – nên đọc lại SRT, sửa tay rồi chạy 'srt2ass'.")
    return {"dong": len(chunks), "tu_tin_cay_thap": len(low)}


def cmd_srt2ass(a: argparse.Namespace) -> None:
    chunks = parse_srt(Path(a.srt))
    if not chunks:
        raise KvtError("SRT trống hoặc sai định dạng.")
    write_ass(chunks, Path(a.output), a.kieu, karaoke=False)
    log(f"Đã tạo {a.output} ({len(chunks)} dòng)")


# ---------------------------------------------------------------- 4. âm thanh


VOICE_CHAIN = ("highpass=f=75,lowpass=f=15500,"
               "afftdn=nr=8:nf=-42:tn=1,"            # khử ồn nhẹ – giữ chất giọng tự nhiên
               "deesser=i=0.35,"
               "acompressor=threshold=-21dB:ratio=2.2:attack=12:release=180:makeup=2")


def loudnorm_measure(src: str, chain: str, target: float, tp: float, lra: float) -> dict:
    proc = subprocess.run([need("ffmpeg"), "-hide_banner", "-nostdin", "-i", src, "-vn", "-af",
                           f"{chain},loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json",
                           "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr, re.S)
    if proc.returncode != 0 or not m:
        raise KvtError("Không đo được âm lượng (loudnorm).")
    return json.loads(m.group(0))


def build_audio(voice_src: str, out_wav: str, music: str | None, music_db: float, duck: bool,
                target: float = -14.0, tp: float = -1.5, lra: float = 11.0, clean: bool = True,
                duration: float | None = None) -> dict:
    """Giọng (làm sạch) + nhạc nền (lặp, mờ dần, tự hạ khi nói) → chuẩn hoá 2 lượt → WAV 48 kHz."""
    vinfo = probe(voice_src)
    dur = duration or duration_of(vinfo)
    voice = VOICE_CHAIN if clean else "anull"
    inputs = ["-i", voice_src]
    if music:
        inputs += ["-stream_loop", "-1", "-i", music]
        fade_out = max(0.0, dur - 2.5)
        graph = (
            f"[0:a]aresample=48000,{voice},asplit=2[v][key0];"
            # tín hiệu điều khiển được chuẩn hoá → mức hạ nhạc (~9–10 dB) không phụ thuộc giọng to/nhỏ
            "[key0]highpass=f=120,dynaudnorm=f=150:g=15:m=20[key];"
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=end={dur:.3f},asetpts=PTS-STARTPTS,"
            f"volume={music_db}dB,afade=t=in:d=1.5,afade=t=out:st={fade_out:.3f}:d=2.5[m];"
        )
        if duck:
            graph += ("[m][key]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400:makeup=1[md];"
                      "[v]aformat=channel_layouts=stereo[vs];[vs][md]amix=inputs=2:duration=first:normalize=0[mix]")
        else:
            graph += "[key]anullsink;[v]aformat=channel_layouts=stereo[vs];[vs][m]amix=inputs=2:duration=first:normalize=0[mix]"
        tmp = out_wav + ".mix.wav"
        run(ffmpeg_base() + inputs + ["-filter_complex", graph, "-map", "[mix]", "-t", f"{dur:.3f}",
                                      "-c:a", "pcm_s24le", tmp])
        stage_src, chain = tmp, "anull"
    else:
        stage_src, chain = voice_src, f"aresample=48000,{voice}"
    meas = loudnorm_measure(stage_src, chain, target, tp, lra)
    ln = (f"loudnorm=I={target}:TP={tp}:LRA={lra}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
          f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:"
          "linear=true")
    run(ffmpeg_base() + ["-i", stage_src, "-vn", "-af", f"{chain},{ln},aresample=48000",
                         "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", out_wav])
    if music:
        os.unlink(stage_src)
    return {"do_vao_LUFS": meas["input_i"], "muc_tieu_LUFS": target}


def cmd_am_thanh(a: argparse.Namespace) -> dict:
    res = build_audio(a.input, a.output, a.nhac, a.muc_nhac, not a.khong_ha_nhac, a.lufs, clean=not a.khong_lam_sach)
    log(f"Đã xuất âm thanh: {a.output} ({res})")
    return res


# ---------------------------------------------------------------- 5. hình ảnh + xuất


GRADES = {
    "khong": "",
    # tự nhiên: tăng nhẹ tương phản & bão hoà, giữ màu da
    "tu-nhien": "eq=contrast=1.04:saturation=1.06:gamma=0.99",
    # huyền bí ấm: vùng tối hơi tím, vùng sáng hơi ấm – vừa phải
    "huyen-bi": "eq=contrast=1.06:saturation=1.05:gamma=0.98,colorbalance=rs=0.02:bs=0.05:rh=0.03:bh=-0.03",
    # sáng sạch cho cảnh thiếu sáng
    "sang": "eq=contrast=1.03:brightness=0.03:saturation=1.05:gamma=0.95",
    # Kendy: sáng, trong, sắc; bóng tối ngả nhẹ xanh cổ vịt, vùng sáng ngả kem – rất nhẹ để giữ màu da và màu lá bài
    "kendy": "eq=brightness=0.035:contrast=1.05:saturation=1.04:gamma=0.96,"
             "colorbalance=rs=-0.02:gs=0.008:bs=0.015:rh=0.015:gh=0.006:bh=-0.012",
}

SHARPEN = {
    "khong": "",
    "nhe": "cas=strength=0.25",
    "vua": "cas=strength=0.45",
    "manh": "cas=strength=0.6,unsharp=5:5:0.3:5:5:0",
}


def parse_card(spec: str) -> tuple[str, float, float]:
    """'anh.jpg@3.5-8' → (anh.jpg, 3.5, 8.0)."""
    m = re.match(r"^(.*)@([\d.]+)-([\d.]+)$", spec)
    if not m:
        raise KvtError(f"Sai cú pháp lá bài '{spec}'. Đúng: duong/dan/la-bai.jpg@BAT_DAU-KET_THUC (giây)")
    path, s, e = m.group(1), float(m.group(2)), float(m.group(3))
    if not Path(path).is_file():
        raise KvtError(f"Không thấy ảnh lá bài: {path}")
    if e <= s:
        raise KvtError(f"Thời gian lá bài không hợp lệ: {spec}")
    return path, s, e


def frame_plan(info: dict, khung: str, tam_x, zoom: float, src: str, need_faces: bool) -> dict:
    """Quyết định khung (tự động nếu cần) + toạ độ cắt + đường đi khuôn mặt trên khung xuất."""
    v = stream(info, "video")
    if not v:
        raise KvtError("Tệp không có hình.")
    w, h = display_size(v)
    track = None
    auto_x = str(tam_x).lower() == "auto"
    if khung == "auto" or auto_x or need_faces:
        try:
            track = bo_cuc.detect_faces(src, w, h)
        except Exception as e:  # thiếu mô hình / OpenCV → vẫn dựng được, chỉ mất tính năng tránh mặt
            log(f"CẢNH BÁO: không nhận diện được khuôn mặt ({e}). Bố cục dùng vị trí mặc định.")
    fx = bo_cuc.main_face_x(track, w) if track else None
    if khung == "auto":
        if h >= w * 1.3:
            khung = "vua"
        else:
            khung = "cat" if fx is not None else "nen-mo"
        log(f"Tự chọn khung: {khung}" + (f" (mặt ở {fx:.2f} chiều ngang)" if fx is not None and khung == "cat" else ""))
    if auto_x:
        tam_x = fx if fx is not None else 0.5
    tam_x = float(tam_x)
    crop = None
    if khung == "cat":
        ch = h / max(zoom, 1.0)
        cw = min(w, ch * 9 / 16)
        if cw >= w:
            cw = w
            ch = min(h, w * 16 / 9)
        cw, ch = int(cw) // 2 * 2, int(ch) // 2 * 2
        x = int(min(max(0, tam_x * w - cw / 2), w - cw))
        y = int((h - ch) / 2)
        crop = (cw, ch, x, y)
    geo = bo_cuc.geometry(khung, w, h, crop)
    faces_out = [(t, [geo.map(b) for b in boxes]) for t, boxes in track] if track else []
    return {"khung": khung, "tam_x": tam_x, "crop": crop, "w": w, "h": h, "faces": faces_out,
            "co_mat": bool(track)}


def video_chain(plan: dict, grade: str, lut: str | None, sharpen: str, fps: float, denoise: bool) -> str:
    khung = plan["khung"]
    f = []
    if denoise:
        f.append("hqdn3d=1.2:1.2:4:4")  # khử nhiễu nhẹ trước khi làm nét (tránh làm nét cả hạt nhiễu)
    if khung == "cat":
        cw, ch, x, y = plan["crop"]
        f.append(f"crop={cw}:{ch}:{x}:{y}")
        f.append(f"scale={OUT_W}:{OUT_H}:flags=lanczos+accurate_rnd+full_chroma_int")
    elif khung == "nen-mo":
        # giữ toàn khung, nền là chính video phóng to làm mờ (hợp cho cảnh trải bài ngang)
        f.append(
            f"split=2[bgsrc][fg];[bgsrc]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
            f"crop={OUT_W}:{OUT_H},boxblur=30:3,eq=brightness=-0.08[bg];"
            f"[fg]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease:flags=lanczos[fg2];"
            f"[bg][fg2]overlay=(W-w)/2:(H-h)/2")
    else:  # 'vua' – nguồn đã dọc
        f.append(f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase:flags=lanczos,crop={OUT_W}:{OUT_H}")
    if lut:
        f.append(f"lut3d=file='{ffpath(lut)}':interp=tetrahedral")
    if GRADES.get(grade):
        f.append(GRADES[grade])
    if SHARPEN.get(sharpen):
        f.append(SHARPEN[sharpen])
    f.append("setsar=1")
    f.append(f"fps={fps:.6f}")
    return ",".join(f)


def parse_timed(spec: str, what: str) -> tuple[str, float, float]:
    """'nội dung@3.5-8' → ('nội dung', 3.5, 8.0)."""
    m = re.match(r"^(.*)@([\d.]+)-([\d.]+)$", spec.strip(), re.S)
    if not m or float(m.group(3)) <= float(m.group(2)):
        raise KvtError(f"Sai cú pháp {what} '{spec}'. Đúng: NOI_DUNG@BAT_DAU-KET_THUC (giây)")
    return m.group(1), float(m.group(2)), float(m.group(3))


def parse_zone(spec: str) -> tuple[bo_cuc.Box, float, float]:
    body, s, e = parse_timed(spec, "vùng tránh")
    try:
        x, y, w, h = [float(v) for v in body.split(",")]
    except ValueError:
        raise KvtError(f"Vùng tránh phải là x,y,rộng,cao@bắt_đầu-kết_thúc (px trên khung 1080×1920): {spec}")
    return bo_cuc.Box(x, y, w, h), s, e


def text_box(lines: list[tuple[str, int]], pad: int = 36) -> tuple[float, float]:
    wmax = max(len(t) * size * 0.56 for t, size in lines)
    hsum = sum(size * 1.3 for _, size in lines)
    return min(OUT_W - bo_cuc.SAFE_LEFT - bo_cuc.SAFE_RIGHT, wmax + 2 * pad), hsum + 2 * pad


def write_overlay_ass(path: Path, items: list[dict]) -> None:
    """Chữ điểm nhấn & CTA theo bảng màu Kendy: hộp xanh cổ vịt trong mờ, chữ kem / champagne."""
    teal = ass_color(KENDY["teal"], 0x30)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hop,Be Vietnam Pro,10,{teal},{teal},{teal},{teal},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Chinh,Be Vietnam Pro,58,{ass_color(KENDY["champagne"])},&H00FFFFFF,{ass_color(KENDY["teal_dam"])},&H00000000,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1
Style: Phu,Be Vietnam Pro,42,{ass_color(KENDY["kem"])},&H00FFFFFF,{ass_color(KENDY["teal_dam"])},&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = []
    for it in items:
        b, s, e = it["box"], it["s"], it["e"]
        fad = r"{\fad(300,300)}"
        x0, y0, x1, y1 = int(b.x), int(b.y), int(b.x + b.w), int(b.y + b.h)
        r = 22  # bo góc
        shape = (f"m {x0 + r} {y0} l {x1 - r} {y0} b {x1} {y0} {x1} {y0} {x1} {y0 + r} l {x1} {y1 - r} "
                 f"b {x1} {y1} {x1} {y1} {x1 - r} {y1} l {x0 + r} {y1} b {x0} {y1} {x0} {y1} {x0} {y1 - r} "
                 f"l {x0} {y0 + r} b {x0} {y0} {x0} {y0} {x0 + r} {y0}")
        rows.append(f"Dialogue: 0,{ass_ts(s)},{ass_ts(e)},Hop,,0,0,0,,{fad}{{\\pos(0,0)\\p1}}{shape}{{\\p0}}")
        # đường chỉ champagne mảnh phía trên chữ
        lx0, lx1, ly = int(b.x + b.w * 0.38), int(b.x + b.w * 0.62), y0 + 16
        rows.append(f"Dialogue: 1,{ass_ts(s)},{ass_ts(e)},Hop,,0,0,0,,{fad}{{\\pos(0,0)\\1c{ass_color(KENDY['champagne'])}&\\p1}}"
                    f"m {lx0} {ly} l {lx1} {ly} l {lx1} {ly + 3} l {lx0} {ly + 3}{{\\p0}}")
        cx = int(b.x + b.w / 2)
        lines = it["lines"]
        total_h = sum(size * 1.3 for _, size in lines)
        y = b.y + (b.h - total_h) / 2 + 6
        for k, (txt, size) in enumerate(lines):
            st = "Chinh" if k == 0 else "Phu"
            cy = int(y + size * 0.65)
            rows.append(f"Dialogue: 2,{ass_ts(s)},{ass_ts(e)},{st},,0,0,0,,{fad}{{\\an5\\pos({cx},{cy})}}{ass_escape(txt)}")
            y += size * 1.3
    path.write_text(head + "\n".join(rows) + "\n", "utf-8")


def hide_subtitles(ass_path: str, windows: list[tuple[float, float]], out: Path) -> str:
    """Ẩn dòng phụ đề trùng thời gian với CTA / điểm nhấn đặt ở dải phụ đề (dòng chỉ chạm mép thì cắt ngắn)."""
    def secs(t: str) -> float:
        h, m, s_ = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s_)

    rows = []
    for line in Path(ass_path).read_text("utf-8").splitlines():
        if line.startswith("Dialogue:"):
            f = line.split(",", 9)
            s0, e0 = secs(f[1]), secs(f[2])
            for ws, we in windows:
                if s0 < we and ws < e0:
                    if s0 < ws - 0.3:        # còn phần trước cửa sổ → kết thúc sớm
                        e0 = ws
                    else:
                        s0 = e0 = -1
            if e0 <= s0:
                continue
            f[2] = ass_ts(e0)
            line = ",".join(f)
        rows.append(line)
    out.write_text("\n".join(rows) + "\n", "utf-8")
    return str(out)


def cmd_xuat(a: argparse.Namespace) -> dict:
    info = probe(a.input)
    dur = duration_of(info)
    fps = a.fps or (30.0 if abs(fps_of(info) - 29.97) < 0.05 else round(fps_of(info), 3))
    fps = min(max(fps, 24.0), 60.0)
    if a.khung not in ("cat", "nen-mo", "vua", "auto"):
        raise KvtError("--khung phải là: auto | cat | nen-mo | vua")
    if a.mau not in GRADES:
        raise KvtError(f"--mau phải là: {' | '.join(GRADES)}")
    if a.net not in SHARPEN:
        raise KvtError(f"--net phải là: {' | '.join(SHARPEN)}")
    cards = [parse_card(c) for c in (a.la_bai or [])]
    notes = [parse_timed(d, "điểm nhấn") for d in (getattr(a, "diem_nhan", None) or [])]
    zones = [parse_zone(z) for z in (getattr(a, "vung_tranh", None) or [])]
    cta = getattr(a, "cta", None)
    need_faces = bool(cards or notes or cta) and not getattr(a, "khong_tranh_mat", False)
    plan = frame_plan(info, a.khung, a.tam_x, a.zoom, a.input, need_faces)
    chain = video_chain(plan, a.mau, a.lut, a.net, fps, not a.khong_khu_nhieu)
    faces = plan["faces"]

    placed: list[tuple[bo_cuc.Box, float, float]] = []
    layout_log = {"khung": plan["khung"], "tam_x": round(plan["tam_x"], 3), "co_nhan_dien_mat": plan["co_mat"],
                  "muc": []}

    def obstacles(s: float, e: float, with_subs: bool) -> tuple[list[bo_cuc.Box], list[bo_cuc.Box]]:
        hard = [b for b, zs, ze in zones if zs < e and s < ze]
        hard += [b.grow(0.04) for b, ps, pe in placed if ps < e and s < pe]
        soft = [bo_cuc.subtitle_band()] if (with_subs and a.phu_de) else []
        return bo_cuc.obstacles_in(faces, s, e, hard, soft, tranh_tay=not getattr(a, "khong_tranh_tay", False))

    def place_banner(s: float, e: float, bw: float, bh: float, is_cta: bool):
        """Chữ điểm nhấn / CTA. Đặt vào dải phụ đề thì phụ đề tạm ẩn trong lúc đó."""
        cands = bo_cuc.banner_candidates(bw, bh, is_cta)
        hard, soft = obstacles(s, e, False)
        band = [bo_cuc.subtitle_band()] if a.phu_de else []
        for box, hides in cands:  # 1) không chạm gì
            if not any(box.hits(o) for o in hard + soft + ([] if hides else band)):
                return box, hides and bool(a.phu_de), True
        for box, hides in cands:  # 2) không chạm mặt / vùng cấm; ưu tiên thay chỗ phụ đề
            if hides and not any(box.hits(o) for o in hard):
                return box, bool(a.phu_de), False
        box, ok = bo_cuc.choose([c for c, _ in cands], hard, soft + band)
        return box, False, ok

    inputs = ["-i", a.input]
    graph = [f"[0:v]{chain}[base]"]
    last = "base"
    idx = 1
    vien = getattr(a, "vien_la_bai", None)
    # lá bài sắc nét: chèn ảnh gốc độ phân giải cao (không phải hình quay đã phóng to)
    for n, (path, s, e) in enumerate(cards):
        ci = stream(probe(path), "video")
        ratio = int(ci["width"]) / int(ci["height"])
        card_h = OUT_H * a.co_la_bai
        border = 6 if vien else 0
        card_w = card_h * ratio + 2 * border
        if str(a.vi_tri_la_bai).lower() == "auto":
            box, ok = bo_cuc.choose(bo_cuc.card_candidates(card_w, card_h + 2 * border), *obstacles(s, e, True))
            if not ok:
                log(f"CẢNH BÁO: lá bài {Path(path).name} ({s:g}–{e:g}s) không có chỗ trống hoàn toàn – "
                    "đã chọn chỗ chồng ít nhất. Nên giảm --co-la-bai hoặc đổi thời điểm.")
        else:
            cy = OUT_H * float(a.vi_tri_la_bai)
            box, ok = bo_cuc.Box((OUT_W - card_w) / 2, cy - card_h / 2 - border, card_w, card_h + 2 * border), True
        placed.append((box, s, e))
        layout_log["muc"].append({"loai": "la_bai", "tep": Path(path).name, "tu": s, "den": e,
                                  "x": int(box.x), "y": int(box.y), "rong": int(box.w), "cao": int(box.h),
                                  "khong_che": ok})
        inner_h = int(box.h - 2 * border) // 2 * 2
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", path]
        border_f = f"pad=iw+{2 * border}:ih+{2 * border}:{border}:{border}:color=0x{vien.lstrip('#')}," if vien else ""
        graph.append(
            f"[{idx}:v]scale=-2:{inner_h}:flags=lanczos,{border_f}format=rgba,"
            f"pad=iw+60:ih+60:30:30:color=0x00000000,split[cf{n}][cs{n}];"       # chừa chỗ cho bóng mềm
            f"[cs{n}]colorchannelmixer=rr=0:gg=0:bb=0:aa=0.5,boxblur=14:2[sh{n}];"
            f"[sh{n}][cf{n}]overlay=x=-6:y=-10,"
            f"fade=t=in:st={s:.3f}:d=0.35:alpha=1,fade=t=out:st={max(s, e - 0.35):.3f}:d=0.35:alpha=1[card{n}]")
        graph.append(f"[{last}][card{n}]overlay=x={int(box.x) - 30}:y={int(box.y) - 30}:"
                     f"enable='between(t,{s:.3f},{e:.3f})':format=auto[ov{n}]")
        last = f"ov{n}"
        idx += 1

    # chữ điểm nhấn + CTA (chỉ xuất hiện ở nội dung quan trọng do Kendy chỉ định)
    ov_items = []
    hide_windows: list[tuple[float, float]] = []
    for txt, s, e in notes:
        parts = [p.strip() for p in txt.split("|") if p.strip()]
        lines = [(parts[0], 58)] + [(p, 42) for p in parts[1:2]]
        bw, bh = text_box(lines)
        box, hides, ok = place_banner(s, e, bw, bh, False)
        placed.append((box, s, e))
        ov_items.append({"box": box, "s": s, "e": e, "lines": lines})
        if hides:
            hide_windows.append((s, e))
        layout_log["muc"].append({"loai": "diem_nhan", "chu": txt, "tu": s, "den": e, "y": int(box.y),
                                  "thay_cho_phu_de": hides, "khong_che": ok})
    if cta:
        parts = [p.strip() for p in cta.split("|") if p.strip()]
        lines = [(parts[0], 58)] + [(p, 42) for p in parts[1:2]]
        cs = max(0.0, dur - float(getattr(a, "cta_giay", 3.5)))
        bw, bh = text_box(lines)
        box, hides, ok = place_banner(cs, dur, bw, bh, True)
        ov_items.append({"box": box, "s": cs, "e": dur, "lines": lines})
        if hides:
            hide_windows.append((cs, dur))
        layout_log["muc"].append({"loai": "cta", "chu": cta, "tu": round(cs, 2), "den": round(dur, 2),
                                  "y": int(box.y), "thay_cho_phu_de": hides, "khong_che": ok})
    tmp_dir = Path(tempfile.mkdtemp(prefix="kvt-"))
    if a.phu_de:
        if not Path(a.phu_de).is_file():
            raise KvtError(f"Không thấy tệp phụ đề: {a.phu_de}")
        sub = a.phu_de
        if sub.lower().endswith(".srt"):
            tmp_ass = tmp_dir / "sub.ass"
            write_ass(parse_srt(Path(sub)), tmp_ass, style=getattr(a, "kieu_phu_de", "tarot"), karaoke=False)
            sub = str(tmp_ass)
        if hide_windows:
            sub = hide_subtitles(sub, hide_windows, tmp_dir / "sub-an.ass")
        graph.append(f"[{last}]subtitles=filename='{ffpath(sub)}':fontsdir='{ffpath(FONTS_DIR)}'[subbed]")
        last = "subbed"
    if ov_items:
        ov_ass = tmp_dir / "overlay.ass"
        write_overlay_ass(ov_ass, ov_items)
        graph.append(f"[{last}]subtitles=filename='{ffpath(ov_ass)}':fontsdir='{ffpath(FONTS_DIR)}'[olay]")
        last = "olay"
    graph.append(f"[{last}]format=yuv420p[vout]")

    audio_map = []
    if stream(info, "audio"):
        wav = str(tmp_dir / "mix.wav")
        build_audio(a.input, wav, a.nhac, a.muc_nhac, not a.khong_ha_nhac, a.lufs,
                    clean=not a.khong_lam_sach, duration=dur)
        inputs += ["-i", wav]
        audio_map = ["-map", f"{idx}:a", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]

    body = tmp_dir / "body.mp4"
    out = Path(a.output)
    target = body if (a.intro or a.outro) else out
    enc = ["-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf), "-profile:v", "high", "-level:v", "4.2",
           "-pix_fmt", "yuv420p", "-g", str(int(round(fps * 2))), "-bf", "2",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
           "-fps_mode", "cfr", "-r", f"{fps:.6f}", "-movflags", "+faststart"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(";\n".join(graph))
        script = fh.name
    try:
        log(f"Đang dựng hình 9:16 ({fps:g} khung/giây, {dur:.1f}s, khung {plan['khung']})…")
        run(ffmpeg_base() + inputs + ["-filter_complex_script", script, "-map", "[vout]"] + audio_map + enc +
            ["-t", f"{dur:.3f}", str(target)])
    finally:
        os.unlink(script)
    if a.intro or a.outro:
        join_clips([p for p in (a.intro, str(body), a.outro) if p], out, fps, enc,
                   xf=float(getattr(a, "chuyen_canh", 0.4) or 0.4))
    shutil.rmtree(tmp_dir, ignore_errors=True)
    out.with_suffix(".bo-cuc.json").write_text(json.dumps(layout_log, ensure_ascii=False, indent=1), "utf-8")
    bad = [m for m in layout_log["muc"] if not m.get("khong_che", True)]
    if bad:
        log(f"CẢNH BÁO: {len(bad)} mục có thể chồng lên mặt / phụ đề – xem {out.with_suffix('.bo-cuc.json').name}")
    log(f"Đã xuất: {out}")
    return cmd_kiem_tra(argparse.Namespace(input=str(out), lufs=a.lufs, in_json=False))


def join_clips(clips: list[str], out: Path, fps: float, enc: list[str], xf: float = 0.4) -> None:
    """Nối các đoạn (intro / thân / outro / cảnh): đưa về cùng chuẩn rồi chuyển cảnh mờ chồng xf giây."""
    inputs, parts = [], []
    durs = []
    for i, c in enumerate(clips):
        ci = probe(c)
        durs.append(duration_of(ci))
        inputs += ["-i", c]
        parts.append(f"[{i}:v]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                     f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps:.6f},format=yuv420p,"
                     f"settb=AVTB[v{i}]")
        if stream(ci, "audio"):
            parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=end={durs[-1]:.3f}[a{i}]")
        else:
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=end={durs[-1]:.3f}[a{i}]")
    vlast, alast, offset = "v0", "a0", durs[0]
    for i in range(1, len(clips)):
        d = max(1.0 / fps, min(xf, durs[i - 1] / 3, durs[i] / 3))
        offset -= d
        parts.append(f"[{vlast}][v{i}]xfade=transition=fade:duration={d:.4f}:offset={offset:.4f}[vx{i}]")
        parts.append(f"[{alast}][a{i}]acrossfade=d={d:.4f}[ax{i}]")
        vlast, alast = f"vx{i}", f"ax{i}"
        offset += durs[i]
    run(ffmpeg_base() + inputs + ["-filter_complex", ";".join(parts), "-map", f"[{vlast}]", "-map", f"[{alast}]"]
        + enc + ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])


# ---------------------------------------------------------------- 6. kiểm tra


def cmd_kiem_tra(a: argparse.Namespace) -> dict:
    info = probe(a.input)
    v = stream(info, "video")
    au = stream(info, "audio")
    res: dict = {"tep": a.input, "dung_luong_MB": round(int(info["format"]["size"]) / 1e6, 1),
                 "thoi_luong_giay": round(duration_of(info), 2)}
    problems = []
    if v:
        w, h = display_size(v)
        res.update({"rong": w, "cao": h, "khung_hinh_giay": round(fps_of(info), 3), "ma_hoa": v["codec_name"],
                    "profile": v.get("profile"), "pix_fmt": v.get("pix_fmt")})
        if (w, h) != (OUT_W, OUT_H):
            problems.append(f"kích thước {w}×{h} ≠ 1080×1920")
        if v.get("pix_fmt") != "yuv420p":
            problems.append("pix_fmt không phải yuv420p (điện thoại có thể không phát)")
    else:
        problems.append("không có hình")
    if au:
        meas = loudnorm_measure(a.input, "anull", -14, -1.5, 11)
        res.update({"am_luong_LUFS": float(meas["input_i"]), "dinh_dB": float(meas["input_tp"]),
                    "tan_so_mau": int(au["sample_rate"])})
        if abs(float(meas["input_i"]) - a.lufs) > 1.5:
            problems.append(f"âm lượng {meas['input_i']} LUFS lệch mục tiêu {a.lufs}")
        if float(meas["input_tp"]) > -0.5:
            problems.append("đỉnh âm thanh quá cao, có thể rè")
    else:
        problems.append("không có âm thanh")
    res["dat"] = not problems
    res["van_de"] = problems
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


# ---------------------------------------------------------------- 7. ghép cảnh, lồng tiếng, từ điển, motion


def replace_audio(video: str, voice: str, out: str) -> None:
    """Thay âm thanh video bằng tệp lồng tiếng; hình dài thêm (giữ khung cuối) hoặc cắt bớt cho khớp lời."""
    vd, ad = duration_of(probe(video)), duration_of(probe(voice))
    pad = max(0.0, ad - vd)
    vf = f"tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else "null"
    run(ffmpeg_base() + ["-i", video, "-i", voice, "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "1:a:0",
                         "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p",
                         "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-t", f"{ad:.3f}", out])


def cmd_ghep_canh(a: argparse.Namespace) -> str:
    scenes = []
    for item in a.canh:
        k = canh.kind_of(item.split("@")[0])
        if k == "am-thanh":
            raise KvtError(f"'{item}' là âm thanh – dùng --long-tieng cho tệp lồng tiếng.")
        if k == "anh":
            path, _, sec = item.partition("@")
            scenes.append({"anh": path, **({"giay": float(sec)} if sec else {})})
        else:
            path, _, rng = item.partition("@")
            sc = {"video": path}
            if rng:
                t0, _, t1 = rng.partition("-")
                sc.update({"tu": float(t0 or 0), **({"den": float(t1)} if t1 else {})})
            scenes.append(sc)
    return build_scenes(scenes, a.long_tieng, a.output, fps=a.fps or 30.0, zoom=not a.khong_chuyen_dong,
                        xf=a.chuyen_canh)


def build_scenes(scenes: list[dict], voice: str | None, out: str, fps: float = 30.0, zoom: bool = True,
                 xf: float = 0.4) -> str:
    if not scenes:
        raise KvtError("Chưa có cảnh nào.")
    for sc in scenes:
        p = sc.get("anh") or sc.get("video")
        if not p or not Path(p).is_file():
            raise KvtError(f"Không thấy tệp cảnh: {p}")
    if voice and not Path(voice).is_file():
        raise KvtError(f"Không thấy tệp lồng tiếng: {voice}")
    voice_dur = duration_of(probe(voice)) if voice else None
    durs = canh.plan_durations(scenes, voice_dur, lambda p: duration_of(probe(p)), xf)
    tmp = Path(tempfile.mkdtemp(prefix="kvt-canh-"))
    clips = []
    enc_mid = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", f"{fps:.6f}",
               "-fps_mode", "cfr", "-movflags", "+faststart"]
    try:
        for i, (sc, d) in enumerate(zip(scenes, durs)):
            c = str(tmp / f"canh{i:03d}.mp4")
            if "anh" in sc:
                log(f"Cảnh {i + 1}: ảnh {Path(sc['anh']).name} – {d:.1f}s")
                canh.image_clip(sc["anh"], c, d, fps, zoom and sc.get("chuyen_dong", True))
            else:
                info = probe(sc["video"])
                plan = frame_plan(info, sc.get("khung", "auto"), sc.get("tam_x", "auto"), 1.0, sc["video"], False)
                chain = video_chain(plan, "khong", None, "khong", fps, False)
                t0 = float(sc.get("tu", 0))
                log(f"Cảnh {i + 1}: video {Path(sc['video']).name} {t0:.1f}–{t0 + d:.1f}s (khung {plan['khung']})")
                amap = ["-map", "0:a:0", "-c:a", "aac", "-b:a", "256k", "-ar", "48000"] if stream(info, "audio") else []
                run(ffmpeg_base() + ["-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", sc["video"], "-filter_complex",
                                     f"[0:v]{chain}[v]", "-map", "[v]"] + amap + enc_mid + [c])
            clips.append(c)
        joined = str(tmp / "noi.mp4")
        if len(clips) > 1:
            join_clips(clips, Path(joined), fps, enc_mid, xf=xf)
        else:
            shutil.copy(clips[0], joined)
        if voice:
            replace_audio(joined, voice, out)
        else:
            shutil.copy(joined, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log(f"Đã ghép {len(scenes)} cảnh → {out}")
    return out


def cmd_tim_mat(a: argparse.Namespace) -> dict:
    info = probe(a.input)
    v = stream(info, "video")
    if not v:
        raise KvtError("Tệp không có hình.")
    w, h = display_size(v)
    track = bo_cuc.detect_faces(a.input, w, h)
    have = sum(1 for _, b in track if b)
    res = {"khung_hinh_da_xet": len(track), "co_mat": have, "tam_x_mat": bo_cuc.main_face_x(track, w),
           "goi_y_khung": "vua" if h >= w * 1.3 else ("cat" if bo_cuc.main_face_x(track, w) is not None else "nen-mo")}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


def cmd_goi_y(a: argparse.Namespace) -> list:
    segs = json.loads(Path(a.tu_json).read_text("utf-8"))
    lv = [x.strip() for x in a.linh_vuc.split(",") if x.strip()]
    gy = tu_dien.suggest(segs, lv)
    out = Path(a.output or Path(a.tu_json).with_suffix("").with_suffix(".goi-y.json"))
    out.write_text(json.dumps(gy, ensure_ascii=False, indent=1), "utf-8")
    for g in gy:
        log(f"{g['thoi_diem']:7.2f}s  «{g['nghe_duoc']}» → gợi ý «{g['goi_y']}» ({g['loai']}, {g['linh_vuc']})")
    log(f"{len(gy)} gợi ý → {out} (chưa sửa gì; Kendy đánh dấu \"dong_y\": true cho mục đồng ý)")
    return gy


def cmd_sua_phu_de(a: argparse.Namespace) -> None:
    segs = json.loads(Path(a.tu_json).read_text("utf-8"))
    gy = json.loads(Path(a.goi_y).read_text("utf-8"))
    segs, n = tu_dien.apply_accepted(segs, gy)
    stem = Path(a.output_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    Path(str(stem) + ".words.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), "utf-8")
    chunks = chunk_words(segs, 30, 3.2)
    write_srt(chunks, Path(str(stem) + ".srt"))
    write_ass(chunks, Path(str(stem) + ".ass"), a.kieu)
    log(f"Đã áp dụng {n} sửa đổi Kendy đồng ý → {stem}.srt / .ass")


def cmd_doi_chieu(a: argparse.Namespace) -> dict:
    segs = json.loads(Path(a.tu_json).read_text("utf-8"))
    script = Path(a.loi_goc).read_text("utf-8")
    new_segs, rep = tu_dien.align_script(segs, script)
    stem = Path(a.output_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    Path(str(stem) + ".doi-chieu.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), "utf-8")
    log(f"Đối chiếu: {rep['so_tu_loi_goc']} từ lời gốc, khác {rep['ty_le_khac']:.1%}, {len(rep['khac_biet'])} chỗ khác "
        f"→ {stem}.doi-chieu.json")
    if not a.chi_bao_cao:
        Path(str(stem) + ".words.json").write_text(json.dumps(new_segs, ensure_ascii=False, indent=1), "utf-8")
        chunks = chunk_words(new_segs, 30, 3.2)
        write_srt(chunks, Path(str(stem) + ".srt"))
        write_ass(chunks, Path(str(stem) + ".ass"), a.kieu)
        log(f"Phụ đề theo LỜI GỐC (mốc thời gian từ Whisper) → {stem}.srt / .ass")
    return rep


def cmd_intro(a: argparse.Namespace) -> str:
    out = motion.remotion("TarotIntro", a.output, {"tieuDe": a.tieu_de, "phuDe": a.phu_de}, a.anh)
    log(f"Đã dựng intro: {out}")
    return out


def cmd_the_bai(a: argparse.Namespace) -> str:
    out = motion.remotion("LaBaiReveal", a.output, {"tenLaBai": a.ten, "yNghia": a.y_nghia}, a.anh)
    log(f"Đã dựng thẻ lá bài: {out}")
    return out


def cmd_outro(a: argparse.Namespace) -> str:
    v = {k: val for k, val in (("thuongHieu", a.thuong_hieu), ("loiMoi", a.loi_moi), ("ghiChu", a.ghi_chu)) if val is not None}
    out = motion.hyperframes_outro(a.output, v, a.anh)
    log(f"Đã dựng outro: {out}")
    return out


# ---------------------------------------------------------------- 8. quy trình đầy đủ


PRESETS_DIR = ROOT / "presets"


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text("utf-8"))
    style = cfg.get("phong_cach")
    if style:
        pf = PRESETS_DIR / f"{style}.json"
        if not pf.is_file():
            raise KvtError(f"Không có phong cách '{style}'. Có: {', '.join(p.stem for p in PRESETS_DIR.glob('*.json'))}")
        cfg = deep_merge(json.loads(pf.read_text("utf-8")), cfg)
    return cfg


def cmd_dung(a: argparse.Namespace) -> dict:
    cfg_path = Path(a.cau_hinh).resolve()
    cfg = load_config(cfg_path)
    base = cfg_path.parent

    def path(v):
        return str((base / v).resolve()) if isinstance(v, str) and v else None

    work = base / cfg.get("thu_muc_tam", "lam-viec")
    work.mkdir(parents=True, exist_ok=True)
    cl = cfg.get("cat_lang_tham_so", {})
    pd = cfg.get("phu_de_tham_so", {})
    x = cfg.get("xuat", {})
    do_cut = cfg.get("cat_lang", True)
    voice = path(cfg.get("long_tieng"))

    def cut(src: str, out: str) -> dict:
        return cmd_cat_lang(argparse.Namespace(
            input=src, output=out, che_do=cl.get("che_do", "auto"), nguong=cl.get("nguong", "auto"),
            lang_toi_thieu=cl.get("lang_toi_thieu", 0.55), dem=cl.get("dem", 0.18), chuyen_mo=cl.get("chuyen_mo", 0),
            giu_toi_thieu=cl.get("giu_toi_thieu", 0.12), chi_xem=False, mo_hinh=pd.get("mo_hinh", "turbo"),
            ngon_ngu=pd.get("ngon_ngu", "vi")))

    words_json = None
    # 1) nguồn: cảnh (ảnh/video) + lồng tiếng, hoặc một video
    if cfg.get("canh"):
        if voice and do_cut:
            cut_voice = str(work / "01-long-tieng-cat.wav")
            cut(voice, cut_voice)
            voice, do_cut = cut_voice, False
        scenes = []
        for sc in cfg["canh"]:
            sc = dict(sc)
            for k in ("anh", "video"):
                if k in sc:
                    sc[k] = path(sc[k])
            scenes.append(sc)
        src = build_scenes(scenes, voice, str(work / "02-ghep-canh.mp4"), zoom=cfg.get("chuyen_dong_anh", True),
                           xf=float(cfg.get("chuyen_canh", 0.4)))
    else:
        src = path(cfg.get("video"))
        if not src:
            raise KvtError("Cấu hình cần 'video' hoặc 'canh'.")
        mic = path(cfg.get("am_thanh_rieng"))
        if voice and cfg.get("long_tieng_che_do", "thay") == "dong-bo":
            mic = voice
            voice = None
        if mic:
            synced = str(work / "01-dong-bo.mp4")
            cmd_dong_bo(argparse.Namespace(video=src, am_thanh=mic, giay_phan_tich=90, output=synced))
            src = synced
        if voice:  # lồng tiếng thay âm thanh gốc
            if do_cut:
                cut_voice = str(work / "01-long-tieng-cat.wav")
                cut(voice, cut_voice)
                voice, do_cut = cut_voice, False
            replaced = str(work / "02-long-tieng.mp4")
            replace_audio(src, voice, replaced)
            src = replaced
    if do_cut:
        rep = cut(src, str(work / "03-cat-lang.mp4"))
        words_json = rep.get("tu_json")
        src = str(work / "03-cat-lang.mp4")

    # 2) phụ đề
    sub = path(cfg.get("phu_de_sua"))
    lv = pd.get("linh_vuc") or []
    if isinstance(lv, str):
        lv = [lv]
    if not sub and cfg.get("phu_de", True):
        cmd_phu_de(argparse.Namespace(
            input=src, thu_muc=str(work), mo_hinh=pd.get("mo_hinh", "turbo"), tu_json=words_json,
            ngon_ngu=pd.get("ngon_ngu", "vi"), goi_y=pd.get("goi_y"), khong_goi_y=False, linh_vuc=",".join(lv),
            ky_tu_toi_da=pd.get("ky_tu_toi_da", 30), giay_toi_da=pd.get("giay_toi_da", 3.2),
            kieu=pd.get("kieu", "tarot"), khong_nhan_tu=not pd.get("nhan_tu", True)))
        stem = work / Path(src).stem
        sub = str(stem) + ".ass"
        if cfg.get("loi_goc"):
            cmd_doi_chieu(argparse.Namespace(tu_json=str(stem) + ".words.json", loi_goc=path(cfg["loi_goc"]),
                                             output_stem=str(stem) + "-loi-goc", kieu=pd.get("kieu", "tarot"),
                                             chi_bao_cao=False))
            sub = str(stem) + "-loi-goc.ass"

    # 3) intro / outro: tệp có sẵn, hoặc tự dựng ({"tao": true, ...}); không bắt buộc
    def clip(key: str) -> str | None:
        v = cfg.get(key)
        if not v:
            return None
        if isinstance(v, str):
            return path(v)
        if v.get("tao"):
            out = str(work / f"{key}.mp4")
            if key == "intro":
                motion.remotion("TarotIntro", out, {"tieuDe": v.get("tieu_de", "THÔNG ĐIỆP TAROT"),
                                                    "phuDe": v.get("phu_de", "Kendy Huyền Học")}, path(v.get("anh")))
            else:
                motion.hyperframes_outro(out, {k2: v[k1] for k1, k2 in (("thuong_hieu", "thuongHieu"),
                                                                         ("loi_moi", "loiMoi"), ("ghi_chu", "ghiChu"))
                                               if k1 in v}, path(v.get("anh")))
            return out
        return None

    cards = [f"{path(c['anh'])}@{c['bat_dau']}-{c['ket_thuc']}" for c in cfg.get("la_bai", [])]
    notes = [f"{d['chu']}{'|' + d['phu'] if d.get('phu') else ''}@{d['bat_dau']}-{d['ket_thuc']}"
             for d in cfg.get("diem_nhan", [])]
    zones = [f"{z['x']},{z['y']},{z['rong']},{z['cao']}@{z['bat_dau']}-{z['ket_thuc']}" for z in cfg.get("vung_tranh", [])]
    cta = cfg.get("cta") or None
    return cmd_xuat(argparse.Namespace(
        input=src, output=str((base / cfg.get("ket_qua", "ket-qua.mp4")).resolve()), khung=x.get("khung", "auto"),
        tam_x=x.get("tam_x", "auto"), zoom=x.get("zoom", 1.0), mau=x.get("mau", "tu-nhien"), lut=path(x.get("lut")),
        net=x.get("net", "nhe"), fps=x.get("fps"), khong_khu_nhieu=not x.get("khu_nhieu", True),
        la_bai=cards, co_la_bai=x.get("co_la_bai", 0.36), vi_tri_la_bai=x.get("vi_tri_la_bai", "auto"),
        vien_la_bai=x.get("vien_la_bai"), diem_nhan=notes, vung_tranh=zones,
        cta=(f"{cta['chu']}|{cta['phu']}" if cta and cta.get("phu") else (cta or {}).get("chu")),
        cta_giay=(cta or {}).get("giay", 3.5), phu_de=sub, kieu_phu_de=pd.get("kieu", "tarot"),
        nhac=path(cfg.get("nhac")), muc_nhac=cfg.get("muc_nhac_dB", -20), khong_ha_nhac=not cfg.get("ha_nhac", True),
        lufs=cfg.get("lufs", -14), khong_lam_sach=not cfg.get("lam_sach_giong", True), intro=clip("intro"),
        outro=clip("outro"), chuyen_canh=cfg.get("chuyen_canh", 0.4), crf=x.get("crf", 18),
        preset=x.get("preset", "slow")))


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="kvt", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("probe", help="xem thông số tệp")
    s.add_argument("input")

    s = sp.add_parser("cat-lang", help="cắt khoảng lặng (video hoặc tệp âm thanh)")
    s.add_argument("input")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--che-do", default="auto", help="auto | am-luong (nhanh) | loi-noi (Whisper, khi có nhạc nền)")
    s.add_argument("--nguong", default="auto", help="ngưỡng im lặng dB hoặc 'auto' (mặc định: tự tính)")
    s.add_argument("--mo-hinh", default="turbo", help="mô hình Whisper cho chế độ loi-noi")
    s.add_argument("--ngon-ngu", default="vi")
    s.add_argument("--lang-toi-thieu", type=float, default=0.55, help="khoảng lặng ngắn nhất bị cắt (giây)")
    s.add_argument("--dem", type=float, default=0.18, help="đệm giữ lại hai đầu câu (giây)")
    s.add_argument("--giu-toi-thieu", type=float, default=0.12, help="bỏ tiếng động ngắn hơn (giây)")
    s.add_argument("--chuyen-mo", type=float, default=0, help="mờ chồng ở điểm cắt (giây, ví dụ 0.1); 0 = cắt thẳng")
    s.add_argument("--chi-xem", action="store_true", help="chỉ in danh sách đoạn, không xuất")

    s = sp.add_parser("dong-bo", help="đồng bộ micro rời / lồng tiếng cùng buổi quay với video")
    s.add_argument("video")
    s.add_argument("am_thanh")
    s.add_argument("-o", "--output")
    s.add_argument("--giay-phan-tich", type=float, default=90)

    s = sp.add_parser("long-tieng", help="thay âm thanh video bằng tệp lồng tiếng WAV/MP3")
    s.add_argument("video")
    s.add_argument("am_thanh")
    s.add_argument("-o", "--output", required=True)

    s = sp.add_parser("ghep-canh", help="ghép video / ảnh (+ lồng tiếng) thành video dọc")
    s.add_argument("canh", nargs="+", help="anh.jpg[@giây] | video.mp4[@từ-đến] theo thứ tự")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--long-tieng", help="tệp lời thoại / lồng tiếng WAV, MP3, M4A…")
    s.add_argument("--chuyen-canh", type=float, default=0.4)
    s.add_argument("--khong-chuyen-dong", action="store_true", help="ảnh đứng yên (không phóng chậm)")
    s.add_argument("--fps", type=float)

    s = sp.add_parser("phu-de", help="nhận dạng lời nói → phụ đề")
    s.add_argument("input")
    s.add_argument("--thu-muc")
    s.add_argument("--mo-hinh", default="turbo", help="turbo (chính xác, mặc định) | small (nhanh) | large-v3")
    s.add_argument("--tu-json", help="dùng lời đã nhận dạng sẵn (từ cat-lang --che-do loi-noi)")
    s.add_argument("--ngon-ngu", default="vi")
    s.add_argument("--linh-vuc", help=f"từ điển chuyên ngành, cách nhau dấu phẩy: {','.join(tu_dien.LINH_VUC)}")
    s.add_argument("--goi-y", help="từ vựng gợi ý thêm cho Whisper (tên riêng, thuật ngữ)")
    s.add_argument("--khong-goi-y", action="store_true")
    s.add_argument("--ky-tu-toi-da", type=int, default=30)
    s.add_argument("--giay-toi-da", type=float, default=3.2)
    s.add_argument("--kieu", default="tarot", choices=list(ASS_STYLES))
    s.add_argument("--khong-nhan-tu", action="store_true", help="tắt hiệu ứng tô màu từng từ")

    s = sp.add_parser("srt2ass", help="SRT đã sửa → ASS")
    s.add_argument("srt")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--kieu", default="tarot", choices=list(ASS_STYLES))

    s = sp.add_parser("tu-dien", help="liệt kê chỗ nghi sai thuật ngữ trong phụ đề (chỉ gợi ý)")
    s.add_argument("tu_json")
    s.add_argument("--linh-vuc", default=",".join(tu_dien.LINH_VUC))
    s.add_argument("-o", "--output")

    s = sp.add_parser("sua-phu-de", help="áp dụng những gợi ý Kendy đã đồng ý")
    s.add_argument("tu_json")
    s.add_argument("goi_y")
    s.add_argument("-o", "--output-stem", required=True, help="đường dẫn gốc, không đuôi (tạo .srt/.ass/.words.json)")
    s.add_argument("--kieu", default="tarot", choices=list(ASS_STYLES))

    s = sp.add_parser("doi-chieu", help="đối chiếu phụ đề với lời thoại gốc; dựng phụ đề theo lời gốc")
    s.add_argument("tu_json")
    s.add_argument("loi_goc", help="tệp văn bản lời thoại gốc (UTF-8)")
    s.add_argument("-o", "--output-stem", required=True)
    s.add_argument("--kieu", default="tarot", choices=list(ASS_STYLES))
    s.add_argument("--chi-bao-cao", action="store_true", help="chỉ báo cáo khác biệt, không tạo phụ đề mới")

    s = sp.add_parser("am-thanh", help="làm sạch giọng + nhạc nền + chuẩn âm lượng")
    s.add_argument("input")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--nhac")
    s.add_argument("--muc-nhac", type=float, default=-20, help="mức nhạc nền (dB, mặc định -20)")
    s.add_argument("--khong-ha-nhac", action="store_true")
    s.add_argument("--khong-lam-sach", action="store_true")
    s.add_argument("--lufs", type=float, default=-14)

    s = sp.add_parser("tim-mat", help="nhận diện khuôn mặt, gợi ý khung 9:16")
    s.add_argument("input")

    s = sp.add_parser("xuat", help="dựng & xuất MP4 dọc 1080×1920")
    s.add_argument("input")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--khung", default="auto", help="auto | cat | nen-mo | vua")
    s.add_argument("--tam-x", default="auto", help="tâm khung cắt theo chiều ngang 0..1 hoặc auto (theo mặt)")
    s.add_argument("--zoom", type=float, default=1.0)
    s.add_argument("--mau", default="tu-nhien", help="|".join(GRADES))
    s.add_argument("--lut", help="tệp .cube tuỳ chọn")
    s.add_argument("--net", default="nhe", help="|".join(SHARPEN))
    s.add_argument("--fps", type=float)
    s.add_argument("--khong-khu-nhieu", action="store_true")
    s.add_argument("--la-bai", action="append", help="anh.jpg@BAT_DAU-KET_THUC (lặp được)")
    s.add_argument("--co-la-bai", type=float, default=0.36, help="chiều cao lá bài / chiều cao khung")
    s.add_argument("--vi-tri-la-bai", default="auto", help="auto (tránh mặt & phụ đề) hoặc tâm dọc 0..1")
    s.add_argument("--vien-la-bai", help="màu viền lá bài, ví dụ #D8BE8C")
    s.add_argument("--diem-nhan", action="append", help="'Chữ chính|chữ phụ@BAT_DAU-KET_THUC' (lặp được)")
    s.add_argument("--cta", help="'Lời kêu gọi|dòng phụ' hiện ở cuối video")
    s.add_argument("--cta-giay", type=float, default=3.5)
    s.add_argument("--vung-tranh", action="append", help="'x,y,rộng,cao@BAT_DAU-KET_THUC' vùng không được che (px)")
    s.add_argument("--khong-tranh-mat", action="store_true")
    s.add_argument("--khong-tranh-tay", action="store_true", help="cho phép đặt chữ/lá bài vào vùng tay cầm bài")
    s.add_argument("--phu-de", help=".ass hoặc .srt")
    s.add_argument("--kieu-phu-de", default="tarot", choices=list(ASS_STYLES), help="dùng khi --phu-de là .srt")
    s.add_argument("--nhac")
    s.add_argument("--muc-nhac", type=float, default=-20)
    s.add_argument("--khong-ha-nhac", action="store_true")
    s.add_argument("--khong-lam-sach", action="store_true")
    s.add_argument("--lufs", type=float, default=-14)
    s.add_argument("--intro")
    s.add_argument("--outro")
    s.add_argument("--chuyen-canh", type=float, default=0.4, help="mờ chồng khi nối intro/outro (giây)")
    s.add_argument("--crf", type=int, default=18)
    s.add_argument("--preset", default="slow")

    s = sp.add_parser("intro", help="dựng intro lật lá bài (Remotion)")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--tieu-de", default="THÔNG ĐIỆP TAROT")
    s.add_argument("--phu-de", default="Kendy Huyền Học")
    s.add_argument("--anh", help="ảnh lá bài")

    s = sp.add_parser("the-bai", help="dựng thẻ giới thiệu lá bài (Remotion)")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--anh", required=True)
    s.add_argument("--ten", required=True)
    s.add_argument("--y-nghia", default="")

    s = sp.add_parser("outro", help="dựng outro / CTA thương hiệu (HyperFrames)")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--thuong-hieu")
    s.add_argument("--loi-moi")
    s.add_argument("--ghi-chu")
    s.add_argument("--anh")

    s = sp.add_parser("kiem-tra", help="kiểm tra tệp xuất")
    s.add_argument("input")
    s.add_argument("--lufs", type=float, default=-14)

    s = sp.add_parser("dung", help="chạy toàn bộ quy trình theo cấu hình JSON")
    s.add_argument("cau_hinh")
    return ap


COMMANDS = {
    "probe": lambda a: print(json.dumps(probe(a.input), ensure_ascii=False, indent=2)),
    "cat-lang": cmd_cat_lang, "dong-bo": cmd_dong_bo, "phu-de": cmd_phu_de, "srt2ass": cmd_srt2ass,
    "am-thanh": cmd_am_thanh, "xuat": cmd_xuat, "kiem-tra": cmd_kiem_tra, "dung": cmd_dung,
    "long-tieng": lambda a: replace_audio(a.video, a.am_thanh, a.output), "ghep-canh": cmd_ghep_canh,
    "tu-dien": cmd_goi_y, "sua-phu-de": cmd_sua_phu_de, "doi-chieu": cmd_doi_chieu, "tim-mat": cmd_tim_mat,
    "intro": cmd_intro, "the-bai": cmd_the_bai, "outro": cmd_outro,
}


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        COMMANDS[a.cmd](a)
    except (KvtError, RuntimeError, FileNotFoundError, ValueError) as e:
        log(f"LỖI: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
