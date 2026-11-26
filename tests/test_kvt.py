"""Kiểm thử tự động cho kvt. Chạy: .venv/bin/python -m unittest discover -s tests -v

Phần "nhanh" chỉ kiểm hàm lõi; phần "tích hợp" tạo video tổng hợp vài giây bằng FFmpeg
(không cần Whisper, không cần mạng)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kvt"))
import kvt  # noqa: E402


class TestLoi(unittest.TestCase):
    def test_speech_segments_pad_merge_snap(self):
        sil = [kvt.Seg(0.0, 1.0), kvt.Seg(2.0, 3.5), kvt.Seg(3.6, 3.65), kvt.Seg(5.0, float("inf"))]
        segs = kvt.speech_segments(sil, 6.0, pad=0.15, min_keep=0.1, fps=30)
        # đoạn nói 1–2 và 3.5–5 (khoảng lặng 3.6–3.65 quá ngắn vẫn tách, rồi được gộp lại nhờ đệm)
        self.assertEqual(len(segs), 2)
        for s in segs:  # ranh giới khớp khung hình
            self.assertAlmostEqual(s.start * 30, round(s.start * 30), places=4)
            self.assertAlmostEqual(s.end * 30, round(s.end * 30), places=4)
        self.assertLessEqual(segs[0].start, 0.85 + 1e-6)
        self.assertGreaterEqual(segs[1].end, 5.15 - 1e-6)

    def test_silences_from_words(self):
        words = [{"s": 0.5, "e": 1.0}, {"s": 1.1, "e": 1.5}, {"s": 3.0, "e": 3.4}]
        sil = kvt.silences_from_words(words, 5.0, 0.5)
        self.assertEqual([(s.start, s.end) for s in sil], [(0.0, 0.5), (1.5, 3.0), (3.4, float("inf"))])

    def test_remap_words(self):
        keep = [kvt.Seg(1.0, 2.0), kvt.Seg(5.0, 6.0)]
        segs = [{"s": 1.2, "e": 5.5, "text": "a b",
                 "words": [{"w": "a", "s": 1.2, "e": 1.5, "p": 1}, {"w": "b", "s": 5.1, "e": 5.5, "p": 1},
                           {"w": "bo", "s": 3.0, "e": 3.2, "p": 1}]}]
        out = kvt.remap_words(segs, keep)
        ws = out[0]["words"]
        self.assertEqual([w["w"] for w in ws], ["a", "b"])  # từ nằm trong đoạn bị cắt thì bỏ
        self.assertAlmostEqual(ws[0]["s"], 0.2)
        self.assertAlmostEqual(ws[1]["s"], 1.1)

    def test_hallucination_filter(self):
        self.assertTrue(kvt.is_hallucination({"text": "Hãy subscribe cho kênh Ghiền Mì Gõ"}))
        self.assertTrue(kvt.is_hallucination({"text": "  "}))
        self.assertFalse(kvt.is_hallucination({"text": "Lá bài Mặt Trăng nói về trực giác",
                                               "no_speech_prob": 0.1, "avg_logprob": -0.3}))

    def test_chunk_no_orphans(self):
        words = [{"w": w, "s": i * 0.4, "e": i * 0.4 + 0.35, "p": 1}
                 for i, w in enumerate("Lá bài hôm nay là Mặt Trăng nhắc bạn tin vào trực giác.".split())]
        chunks = kvt.chunk_words([{"s": 0, "e": 5, "text": "", "words": words}], 30, 3.2)
        self.assertTrue(all(len(c["words"]) >= 3 for c in chunks), [c["text"] for c in chunks])
        self.assertEqual(" ".join(c["text"] for c in chunks), " ".join(w["w"] for w in words))
        for a, b in zip(chunks, chunks[1:]):
            self.assertLessEqual(a["e"], b["s"] + 1e-9)

    def test_srt_roundtrip_and_ass(self):
        chunks = [{"s": 0.5, "e": 2.25, "text": "Thông điệp Tarot hôm nay", "words": []},
                  {"s": 2.25, "e": 4.0, "text": "dành cho bạn", "words": []}]
        with tempfile.TemporaryDirectory() as d:
            srt = Path(d) / "a.srt"
            kvt.write_srt(chunks, srt)
            back = kvt.parse_srt(srt)
            self.assertEqual([c["text"] for c in back], [c["text"] for c in chunks])
            self.assertAlmostEqual(back[0]["s"], 0.5)
            ass = Path(d) / "a.ass"
            kvt.write_ass(back, ass, karaoke=False)
            txt = ass.read_text("utf-8")
            self.assertIn("PlayResX: 1080", txt)
            self.assertIn(r"Thông điệp\NTarot hôm nay", txt)  # tự xuống dòng cân đối

    def test_parse_card(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
            p, s, e = kvt.parse_card(f"{f.name}@3.5-8")
            self.assertEqual((p, s, e), (f.name, 3.5, 8.0))
            with self.assertRaises(kvt.KvtError):
                kvt.parse_card(f"{f.name}@8-3")
        with self.assertRaises(kvt.KvtError):
            kvt.parse_card("khong-co.jpg@1-2")


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class TestTichHop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.src = d / "src.mp4"
        # 8 s video ngang 1280×720 @29.97; âm thanh: nói (tiếng sin điều biên) 0–2 s, lặng 2–4.5 s, nói 4.5–8 s
        ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30000/1001:d=8",
           "-f", "lavfi", "-i",
           "aevalsrc='(lt(t,2)+gte(t,4.5))*0.3*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*3*t))+0.0005*random(0)':s=48000:d=8",
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(cls.src))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_cat_lang_av_sync(self):
        out = Path(self.tmp.name) / "cut.mp4"
        rc = kvt.main(["cat-lang", str(self.src), "-o", str(out)])
        self.assertEqual(rc, 0)
        info = kvt.probe(out)
        v = float(kvt.stream(info, "video")["duration"])
        a = float(kvt.stream(info, "audio")["duration"])
        self.assertLess(abs(v - a), 0.05, "hình và tiếng lệch nhau")
        self.assertTrue(5.6 < v < 6.5, f"thời lượng sau cắt {v}")  # 8 s – ~2.5 s lặng + đệm
        rep = json.loads(out.with_suffix(".cat-lang.json").read_text("utf-8"))
        self.assertEqual(len(rep["doan"]), 2)

    def test_xuat_specs(self):
        out = Path(self.tmp.name) / "doc.mp4"
        rc = kvt.main(["xuat", str(self.src), "-o", str(out), "--preset", "ultrafast", "--khung", "nen-mo"])
        self.assertEqual(rc, 0)
        res = kvt.cmd_kiem_tra(type("A", (), {"input": str(out), "lufs": -14})())
        self.assertEqual((res["rong"], res["cao"]), (1080, 1920))
        self.assertEqual(res["khung_hinh_giay"], 30.0)
        self.assertEqual(res["pix_fmt"], "yuv420p")
        self.assertLess(abs(res["am_luong_LUFS"] + 14), 1.5)

    def test_dong_bo_offset(self):
        d = Path(self.tmp.name)
        mic = d / "mic.wav"
        ff("-i", str(self.src), "-vn", "-af", "adelay=250:all=1,volume=0.5", str(mic))
        off, conf = kvt.find_offset(str(self.src), str(mic), 8)
        self.assertAlmostEqual(off, 0.25, delta=0.003)


if __name__ == "__main__":
    unittest.main()
