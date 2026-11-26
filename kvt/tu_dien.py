"""Từ điển chuyên ngành & đối chiếu phụ đề.

Nguyên tắc: KHÔNG tự sửa nội dung. Bộ công cụ chỉ
  1) gợi ý thuật ngữ cho Whisper nghe đúng chính tả,
  2) liệt kê chỗ nghi nghe nhầm để Kendy duyệt (tệp .goi-y.json, mặc định "dong_y": false),
  3) dựng phụ đề theo LỜI GỐC do Kendy cung cấp (lấy mốc thời gian từ Whisper).
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "tu-dien"
LINH_VUC = ["tarot", "bat-tu-manh-phai", "tu-vi", "phong-thuy", "kinh-dich", "nhan-tuong"]


def nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t)


def strip_marks(t: str) -> str:
    t = unicodedata.normalize("NFD", nfc(t).lower()).replace("đ", "d")
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d")


def tokens(t: str) -> list[str]:
    return re.findall(r"[\w’'-]+", nfc(t), flags=re.UNICODE)


def load(linh_vuc: list[str] | None = None) -> list[dict]:
    out = []
    for name in (linh_vuc or LINH_VUC):
        p = DICT_DIR / f"{name}.json"
        if not p.is_file():
            raise FileNotFoundError(f"Không có từ điển '{name}'. Có: {', '.join(LINH_VUC)}")
        data = json.loads(p.read_text("utf-8"))
        for m in data["muc"]:
            out.append({**m, "linh_vuc": name})
    return out


def whisper_prompt(linh_vuc: list[str], base: str, max_chars: int = 420) -> str:
    """Ghép từ gợi ý cho Whisper (Whisper chỉ đọc ~224 token đầu nên phải ngắn)."""
    parts = [base.strip()] if base else []
    for name in linh_vuc:
        data = json.loads((DICT_DIR / f"{name}.json").read_text("utf-8"))
        parts.append(", ".join(data.get("goi_y_whisper", [])) + ".")
    s = " ".join(p for p in parts if p.strip(" ."))
    return s[:max_chars].rsplit(",", 1)[0] if len(s) > max_chars else s


def _syl_dist(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a.split(), b.split()) if x != y)


# Cặp phụ âm hay nghe lẫn trong tiếng Việt (đầu / cuối âm tiết), so trên dạng bỏ dấu
_INITIALS = ["ngh", "ng", "nh", "ch", "tr", "th", "ph", "kh", "gh", "gi", "qu", "b", "c", "d", "g", "h", "k", "l",
             "m", "n", "p", "r", "s", "t", "v", "x"]
_CONFUSE_INIT = [{"s", "x"}, {"ch", "tr"}, {"d", "gi", "r", "v"}, {"l", "n"}, {"c", "k", "q", "qu"},
                 {"ng", "ngh"}, {"g", "gh"}]
_CONFUSE_FINAL = [("ng", "n"), ("c", "t"), ("nh", "n"), ("ch", "t")]


def _split_initial(syl: str) -> tuple[str, str]:
    for ini in _INITIALS:
        if syl.startswith(ini):
            return ini, syl[len(ini):]
    return "", syl


def _confusable(a: str, b: str) -> bool:
    """Hai âm tiết (đã bỏ dấu) có thể là cùng một âm bị nghe nhầm?"""
    ia, ra = _split_initial(a)
    ib, rb = _split_initial(b)
    if ra == rb and ia != ib:
        return any(ia in g and ib in g for g in _CONFUSE_INIT)
    if ia == ib and ra != rb:
        for x, y in _CONFUSE_FINAL:
            for u, v in ((x, y), (y, x)):
                if ra.endswith(u) and ra[: -len(u)] + v == rb:
                    return True
    return False


def suggest(segs: list[dict], linh_vuc: list[str]) -> list[dict]:
    """Tìm cụm 2–5 âm tiết trong phụ đề giống thuật ngữ (khác dấu, hoặc lệch 1 âm tiết gần giống)."""
    terms = []
    for m in load(linh_vuc):
        for form in [m["chuan"]] + m.get("khac", []):
            n = len(form.split())
            if n >= 2:
                terms.append((strip_marks(form), form, m))
    by_len: dict[int, list] = {}
    for sf, form, m in terms:
        by_len.setdefault(len(sf.split()), []).append((sf, form, m))

    found, seen = [], set()
    for si, seg in enumerate(segs):
        words = seg.get("words") or [{"w": w, "s": seg["s"], "e": seg["e"]} for w in seg["text"].split()]
        toks = [re.sub(r"[^\w’'-]", "", nfc(w["w"]), flags=re.UNICODE) for w in words]
        # vị trí đã khớp ĐÚNG một thuật ngữ (chỉ khác hoa/thường) → không gợi ý chồng lên
        correct: set[int] = set()
        for n, cand in by_len.items():
            for i in range(0, len(toks) - n + 1):
                span = " ".join(toks[i:i + n]).lower()
                if any(span == nfc(form).lower() for _, form, _ in cand):
                    correct.update(range(i, i + n))
        for n, cand in by_len.items():
            for i in range(0, len(toks) - n + 1):
                span = " ".join(toks[i:i + n])
                if not span or correct.intersection(range(i, i + n)):
                    continue
                ss = strip_marks(span)
                for sf, form, m in cand:
                    exact = ss == sf
                    near = False
                    if not exact and n >= 2 and _syl_dist(ss, sf) == 1:
                        x, y = next((x, y) for x, y in zip(ss.split(), sf.split()) if x != y)
                        near = _confusable(x, y)
                    if not (exact or near):
                        continue
                    if exact and span.lower() == nfc(form).lower():
                        continue  # đúng chính tả (chỉ khác hoa/thường) → bỏ qua
                    key = (si, i, form)
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append({
                        "doan": si, "thoi_diem": words[i]["s"], "nghe_duoc": span, "goi_y": m["chuan"],
                        "khop_dang": form, "linh_vuc": m["linh_vuc"], "loai": "sai dấu" if exact else "nghi nghe nhầm",
                        "nguon_thuat_ngu": m.get("nguon", "C"), "dong_y": False})
    return found


def apply_accepted(segs: list[dict], goi_y: list[dict]) -> tuple[list[dict], int]:
    """Chỉ áp dụng mục Kendy đã đánh dấu "dong_y": true."""
    n = 0
    for g in goi_y:
        if not g.get("dong_y"):
            continue
        seg = segs[g["doan"]]
        k = len(g["nghe_duoc"].split())
        new_words = g["goi_y"].split()
        ws = seg.get("words") or []
        for i in range(len(ws) - k + 1):
            span = " ".join(re.sub(r"[^\w’'-]", "", nfc(w["w"]), flags=re.UNICODE) for w in ws[i:i + k])
            if span == g["nghe_duoc"]:
                tail = re.sub(r"^[\w’'-]+", "", ws[i + k - 1]["w"])  # giữ dấu câu sau cụm
                s0, e0 = ws[i]["s"], ws[i + k - 1]["e"]
                step = (e0 - s0) / len(new_words)
                repl = [{"w": w + (tail if j == len(new_words) - 1 else ""), "s": round(s0 + j * step, 3),
                         "e": round(s0 + (j + 1) * step, 3), "p": 1.0} for j, w in enumerate(new_words)]
                seg["words"] = ws[:i] + repl + ws[i + k:]
                seg["text"] = " ".join(w["w"] for w in seg["words"])
                n += 1
                break
    return segs, n


def align_script(segs: list[dict], script: str) -> tuple[list[dict], dict]:
    """Đặt LỜI GỐC lên mốc thời gian Whisper. Trả (đoạn mới, báo cáo khác biệt)."""
    heard = [w for s in segs for w in (s.get("words") or [])]
    if not heard:
        raise ValueError("Cần tệp *.words.json có mốc từng từ (tạo bởi 'kvt phu-de').")
    ref = nfc(script).split()  # giữ nguyên dấu câu của lời gốc
    norm = lambda t: re.sub(r"[^\w]", "", nfc(t).lower(), flags=re.UNICODE)  # noqa: E731
    a = [norm(w["w"]) for w in heard]
    b = [norm(t) for t in ref]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    times: list[tuple[float, float] | None] = [None] * len(ref)
    diffs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(j2 - j1):
                times[j1 + k] = (heard[i1 + k]["s"], heard[i1 + k]["e"])
        elif op in ("replace", "delete", "insert"):
            if i2 > i1 and j2 > j1:  # chia đều khoảng thời gian đã nghe cho các từ gốc
                s0, e0 = heard[i1]["s"], heard[i2 - 1]["e"]
                step = (e0 - s0) / (j2 - j1)
                for k in range(j2 - j1):
                    times[j1 + k] = (s0 + k * step, s0 + (k + 1) * step)
            diffs.append({"loai": {"replace": "khác", "delete": "thừa trong phụ đề", "insert": "thiếu trong phụ đề"}[op],
                          "thoi_diem": round(heard[min(i1, len(heard) - 1)]["s"], 2),
                          "phu_de": " ".join(w["w"] for w in heard[i1:i2]), "loi_goc": " ".join(ref[j1:j2])})
    # từ gốc không nghe thấy: nội suy giữa hai từ lân cận
    for j, t in enumerate(times):
        if t is None:
            prev = next((times[k] for k in range(j - 1, -1, -1) if times[k]), None)
            nxt = next((times[k] for k in range(j + 1, len(times)) if times[k]), None)
            s0 = prev[1] if prev else (nxt[0] - 0.3 if nxt else 0.0)
            e0 = nxt[0] if nxt else s0 + 0.3
            times[j] = (s0, max(s0 + 0.05, min(e0, s0 + 0.35)))
    words = [{"w": ref[j], "s": round(times[j][0], 3), "e": round(times[j][1], 3), "p": 1.0} for j in range(len(ref))]
    # tách câu theo dấu câu của lời gốc để chia đoạn tự nhiên
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?…]$", w["w"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    new_segs = [{"s": c[0]["s"], "e": c[-1]["e"], "text": " ".join(x["w"] for x in c), "words": c} for c in out]
    total = max(1, len(b))
    errors = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")
    rep = {"so_tu_loi_goc": len(b), "so_tu_phu_de": len(a), "ty_le_khac": round(errors / total, 4),
           "khac_biet": diffs}
    return new_segs, rep
