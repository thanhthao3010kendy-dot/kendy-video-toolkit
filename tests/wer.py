"""Tính tỷ lệ lỗi từ (WER) giữa bản nhận dạng và lời gốc – dùng cho kiểm thử Whisper."""
import json, re, sys, unicodedata

def norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    t = re.sub(r"[^\w\s]", " ", t)
    return t.split()

def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r)), len(r)

if __name__ == "__main__":
    ref = " ".join(json.load(open(sys.argv[1], encoding="utf-8")))
    segs = json.load(open(sys.argv[2], encoding="utf-8"))
    hyp = " ".join(s["text"] for s in segs)
    w, n = wer(ref, hyp)
    print(f"WER = {w*100:.1f}% trên {n} từ")
