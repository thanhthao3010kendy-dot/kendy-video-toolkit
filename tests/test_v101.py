"""Kiểm thử phần v1.0.1: tương thích ChatGPT (không mạng, không Whisper, chia đoạn có điểm dừng),
giữ động tác lật bài khi cắt lặng, cân bằng trắng tự động, phụ đề tránh lá bài."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kvt"))
import kvt  # noqa: E402
import phan_tich  # noqa: E402
import tu_dien  # noqa: E402


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class TestPhanTich(unittest.TestCase):
    def test_giam_am_vang(self):
        # ảnh xám trung tính bị phủ vàng (R cao, B thấp) → hệ số phải giảm R, tăng B, trong giới hạn ±12%
        img = np.full((1, 64, 64, 3), (220, 200, 170), np.uint8)  # tường trắng dưới đèn vàng
        c = phan_tich.color_correction(img)
        g = c["he_so_mau"]
        self.assertLess(g["r"], 1.0)
        self.assertGreater(g["b"], 1.0)
        self.assertTrue(all(0.85 <= v <= 1.15 for v in g.values()))
        out = phan_tich.apply_numpy(img[0], c).astype(float).mean((0, 1))
        self.assertLess(out[0] - out[2], 50 - 1)  # chênh đỏ–lam giảm so với ban đầu (50)

    def test_khong_doi_anh_trung_tinh(self):
        img = np.full((1, 32, 32, 3), 120, np.uint8)
        g = phan_tich.color_correction(img)["he_so_mau"]
        self.assertTrue(all(abs(v - 1) < 0.01 for v in g.values()))

    def test_vung_la_bai_nhieu_chi_tiet(self):
        frame = np.full((96, 54, 3), 30, np.uint8)                   # khăn bàn tối
        rng = np.random.default_rng(1)
        frame[40:70, 5:50] = rng.integers(0, 255, (30, 45, 3))       # "lá bài" sặc sỡ nhiều cạnh
        b = phan_tich.busy_map(frame)
        self.assertGreater(b[40:70, 5:50].mean(), 3 * b[0:30].mean() + 0.1)

    def test_dong_tac(self):
        fr = np.zeros((40, 20, 20, 3), np.uint8)
        rng = np.random.default_rng(0)
        for i in range(40):
            fr[i] = rng.integers(0, 10, (20, 20, 3))                 # nhiễu nhẹ (lấp lánh)
        for i in range(20, 28):
            fr[i, :, :10] = 255 * (i % 2)                             # lật bài
        m, thr = phan_tich.motion_profile(fr, 10.0)
        acts = phan_tich.action_intervals(m, thr, 10.0, min_len=0.2)
        self.assertEqual(len(acts), 1)
        self.assertTrue(1.8 <= acts[0][0] <= 2.2 and 2.6 <= acts[0][1] <= 3.0)

    def test_tru_dong_tac_khoi_khoang_lang(self):
        sil = [kvt.Seg(1.0, 5.0)]
        out = kvt.subtract_actions(sil, [(2.5, 3.0)], 0.5, pad=0.25)
        self.assertEqual([(s.start, s.end) for s in out], [(1.0, 2.25), (3.25, 5.0)])


class TestKhongWhisper(unittest.TestCase):
    def test_loi_goc_uoc_luong(self):
        segs = tu_dien.estimate_script_timing("Lá bài hôm nay là Mặt Trăng. Hãy tin trực giác.",
                                              [(0.5, 3.0), (4.0, 6.0)])
        words = [w for s in segs for w in s["words"]]
        self.assertEqual(" ".join(w["w"] for w in words), "Lá bài hôm nay là Mặt Trăng. Hãy tin trực giác.")
        self.assertTrue(all(s["uoc_luong"] for s in segs))
        for w in words:  # không rơi vào khoảng lặng 3–4 s
            self.assertFalse(3.0 < w["s"] < 4.0, w)
        self.assertGreaterEqual(words[0]["s"], 0.5)
        self.assertLessEqual(words[-1]["e"], 6.0)

    def test_ngoai_tuyen_khong_tai(self):
        old = os.environ.get("KVT_NGOAI_TUYEN")
        os.environ["KVT_NGOAI_TUYEN"] = "1"
        try:
            st = kvt.whisper_status("tiny")  # mô hình tiny chưa từng tải
            if st == "thieu-mo-hinh":
                self.assertFalse(kvt.whisper_usable("tiny"))
                with self.assertRaises(kvt.KvtError):
                    kvt.transcribe("x.wav", "tiny", "vi", None)
        finally:
            if old is None:
                del os.environ["KVT_NGOAI_TUYEN"]
            else:
                os.environ["KVT_NGOAI_TUYEN"] = old


class TestTichHop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.d = Path(cls.tmp.name)
        cls.src = d / "src.mp4"
        # 9 s dọc 720×1280: nói 0–2 s, lặng 2–7 s (có "lật bài" 4–5 s), nói 7–9 s
        ff("-f", "lavfi", "-i", "color=c=0x303030:s=720x1280:r=30:d=9",
           "-f", "lavfi", "-i", "testsrc2=s=300x500:r=30:d=9",
           "-f", "lavfi", "-i",
           "aevalsrc='(lt(t,2)+gte(t,7))*0.3*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*3*t))+0.0005*random(0)':s=48000:d=9",
           "-filter_complex", "[0][1]overlay=x='100+300*(t-4)':y=600:enable='between(t,4,5)'[v]", "-map", "[v]", "-map", "2:a",
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(cls.src))
        cls.loi = d / "loi.txt"
        cls.loi.write_text("Xin chào các bạn. Lá bài hôm nay là Mặt Trăng.", "utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_giu_dong_tac_khi_cat_lang(self):
        out = self.d / "cut.mp4"
        self.assertEqual(kvt.main(["cat-lang", str(self.src), "-o", str(out), "--che-do", "am-luong"]), 0)
        rep = json.loads(out.with_suffix(".cat-lang.json").read_text("utf-8"))
        self.assertEqual(len(rep["dong_tac_giu_lai"]), 1)
        a0, a1 = rep["dong_tac_giu_lai"][0]
        self.assertTrue(3.6 <= a0 <= 4.3 and 4.7 <= a1 <= 5.4, rep["dong_tac_giu_lai"])
        kept = rep["doan"]
        self.assertTrue(any(k["bat_dau"] <= 4.0 and k["ket_thuc"] >= 5.0 for k in kept), kept)
        out2 = self.d / "cut2.mp4"
        kvt.main(["cat-lang", str(self.src), "-o", str(out2), "--che-do", "am-luong", "--khong-giu-dong-tac"])
        self.assertLess(kvt.duration_of(kvt.probe(out2)), kvt.duration_of(kvt.probe(out)) - 0.8)

    def test_dung_khong_whisper_chia_doan_diem_dung(self):
        cfg = self.d / "du-an.json"
        cfg.write_text(json.dumps({
            "phong_cach": "kendy", "video": "src.mp4", "loi_goc": "loi.txt", "ket_qua": "ra.mp4",
            "thu_muc_tam": "lv", "phu_de_tham_so": {"mo_hinh": "khong-co-mo-hinh-nay"},
            "cta": {"chu": "Theo dõi Kendy Huyền Học", "giay": 2},
            "xuat": {"preset": "ultrafast", "chia_doan": 3}}, ensure_ascii=False), "utf-8")
        env = dict(os.environ, KVT_NGOAI_TUYEN="1")
        codes = []
        for _ in range(12):
            p = subprocess.run([sys.executable, str(ROOT / "kvt" / "kvt.py"), "--gioi-han-giay", "4", "dung", str(cfg)],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            codes.append(p.returncode)
            if p.returncode != 3:
                break
        self.assertEqual(codes[-1], 0, p.stdout[-1500:])
        self.assertIn(3, codes, "phải có ít nhất một lần tạm dừng")
        info = kvt.probe(self.d / "ra.mp4")
        v = kvt.stream(info, "video")
        self.assertEqual((int(v["width"]), int(v["height"])), (1080, 1920))
        layout = json.loads((self.d / "ra.bo-cuc.json").read_text("utf-8"))
        self.assertNotIn("phu_de_doi_cho", layout, "mốc ước lượng: mặc định KHÔNG ghép phụ đề vào video")
        st = json.loads((self.d / "lv" / "trang-thai.json").read_text("utf-8"))
        self.assertEqual(st["phu-de"]["ket_qua"]["nguon"], "loi-goc-uoc-luong")
        srt = kvt.parse_srt(next((self.d / "lv").glob("*.srt")))
        self.assertEqual(" ".join(c["text"] for c in srt), self.loi.read_text("utf-8"))  # đúng nguyên văn lời gốc
        # chạy lại khi đã xong: không làm lại gì
        p = subprocess.run([sys.executable, str(ROOT / "kvt" / "kvt.py"), "dung", str(cfg)], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn("[xuat] đã xong", p.stdout)

    def test_phu_de_tranh_vung_la_bai(self):
        # nửa dưới đầy "lá bài" sặc sỡ, nửa trên trơn → phụ đề phải chuyển lên
        img = self.d / "bai.mp4"
        ff("-f", "lavfi", "-i", "color=c=0x202020:s=1080x1920:r=30:d=4", "-f", "lavfi", "-i",
           "testsrc2=s=1080x900:r=30:d=4", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", "[0][1]overlay=0:1000[v]", "-map", "[v]", "-map", "2:a", "-t", "4",
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(img))
        srt = self.d / "a.srt"
        srt.write_text("1\n00:00:00,500 --> 00:00:03,000\nThông điệp Tarot\n", "utf-8")
        out = self.d / "bai_ra.mp4"
        self.assertEqual(kvt.main(["xuat", str(img), "-o", str(out), "--preset", "ultrafast", "--phu-de", str(srt)]), 0)
        moved = json.loads(out.with_suffix(".bo-cuc.json").read_text("utf-8"))["phu_de_doi_cho"]
        self.assertEqual(moved["duoi"], 0, moved)
        self.assertEqual(moved["tren"], 1, moved)

    def test_hai_phong_cach_mau(self):
        for name, mau in (("kendy", "kendy-tu-dong"), ("kendy-mau-cu", "kendy")):
            cfg = self.d / f"{name}.json"
            cfg.write_text(json.dumps({"phong_cach": name, "video": "src.mp4"}), "utf-8")
            self.assertEqual(kvt.load_config(cfg)["xuat"]["mau"], mau)

    def test_moi_truong(self):
        res = kvt.cmd_moi_truong(type("A", (), {"khong_thu_mang": True})())
        self.assertTrue(res["chuc_nang"]["xuat_mp4_916"])
        self.assertIn(res["moi_truong"]["nhan_dien_mat"], ("yunet", "haar", "khong"))

    def test_yunet_dong_goi(self):
        m = ROOT / "assets" / "models" / "face_detection_yunet_2023mar.onnx"
        self.assertTrue(m.is_file() and m.stat().st_size < 300_000)
        self.assertTrue((ROOT / "assets" / "models" / "LICENSE-YuNet.txt").is_file())


if __name__ == "__main__":
    unittest.main()
