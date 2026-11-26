"""Kiểm thử phần mở rộng v1: từ điển, đối chiếu lời gốc, bố cục tránh mặt, chuyển cảnh mờ, ghép ảnh + lồng tiếng,
điểm nhấn / CTA, phong cách Kendy, motion graphics. Không cần mạng, không cần Whisper.

Bỏ qua phần dựng Remotion/HyperFrames (chậm ~40 s): đặt biến KVT_BO_QUA_MOTION=1."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kvt"))
import bo_cuc  # noqa: E402
import kvt  # noqa: E402
import tu_dien  # noqa: E402


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def words(text, t0=0.0, step=0.4):
    return [{"w": w, "s": round(t0 + i * step, 3), "e": round(t0 + i * step + 0.35, 3), "p": 0.9}
            for i, w in enumerate(text.split())]


class TestTuDien(unittest.TestCase):
    def test_du_lieu_day_du(self):
        tarot = json.loads((ROOT / "tu-dien" / "tarot.json").read_text("utf-8"))
        cards = [m for m in tarot["muc"] if m["nhom"].startswith("Ẩn")]
        self.assertEqual(len(cards), 78)
        self.assertEqual(len({m["khac"][0] for m in cards}), 78)  # 78 tên tiếng Anh khác nhau
        kd = json.loads((ROOT / "tu-dien" / "kinh-dich.json").read_text("utf-8"))
        self.assertEqual(sum(1 for m in kd["muc"] if m["nhom"].startswith("Quẻ ")), 64)
        for name in tu_dien.LINH_VUC:
            d = json.loads((ROOT / "tu-dien" / f"{name}.json").read_text("utf-8"))
            self.assertIn("Chờ Kendy xác nhận", d["trang_thai"])
            self.assertTrue(d["goi_y_whisper"])

    def test_manh_phai_dung_cach_viet_ung_dung(self):
        mp = json.loads((ROOT / "tu-dien" / "bat-tu-manh-phai.json").read_text("utf-8"))
        terms = {m["chuan"] for m in mp["muc"]}
        for t in ("Tỵ", "Mão", "Thất Sát", "Tố Công", "Đảng Thế", "Đăng thế", "Môn hộ", "Giáp Tý", "Quý Hợi"):
            self.assertIn(t, terms)

    def test_goi_y_khong_tu_sua(self):
        segs = [{"s": 0, "e": 5, "text": "", "words": words("lá bài the moon và thất xát trong lá số, sức mạnh lớn")}]
        before = json.dumps(segs, ensure_ascii=False)
        gy = tu_dien.suggest(segs, ["tarot", "bat-tu-manh-phai"])
        self.assertEqual(json.dumps(segs, ensure_ascii=False), before, "suggest không được sửa dữ liệu")
        pairs = {(g["nghe_duoc"], g["goi_y"]) for g in gy}
        self.assertIn(("thất xát", "Thất Sát"), pairs)
        self.assertTrue(all(g["dong_y"] is False for g in gy))
        # "sức mạnh" đúng chính tả, chỉ khác hoa/thường → không gợi ý
        self.assertFalse(any(g["nghe_duoc"] == "sức mạnh" for g in gy))

    def test_chi_ap_dung_muc_dong_y(self):
        segs = [{"s": 0, "e": 5, "text": "", "words": words("gặp thất xát và tham lan")}]
        gy = tu_dien.suggest(segs, ["bat-tu-manh-phai", "tu-vi"])
        new, n = tu_dien.apply_accepted(json.loads(json.dumps(segs)), gy)
        self.assertEqual(n, 0)
        for g in gy:
            if g["goi_y"] == "Thất Sát":
                g["dong_y"] = True
        new, n = tu_dien.apply_accepted(new, gy)
        self.assertEqual(n, 1)
        self.assertIn("Thất Sát", new[0]["text"])
        self.assertIn("tham lan", new[0]["text"])  # mục chưa đồng ý giữ nguyên

    def test_doi_chieu_loi_goc(self):
        heard = words("hôm nay lá bài mặt trăng nhắt bạn tin vào trực giác")
        segs = [{"s": 0, "e": 5, "text": "", "words": heard}]
        script = "Hôm nay, lá bài Mặt Trăng nhắc bạn hãy tin vào trực giác."
        new, rep = tu_dien.align_script(segs, script)
        text = " ".join(w["w"] for s in new for w in s["words"])
        self.assertEqual(text, script)  # phụ đề mới là ĐÚNG lời gốc
        self.assertTrue(any(d["loai"] == "khác" for d in rep["khac_biet"]))
        self.assertTrue(any(d["loai"] == "thiếu trong phụ đề" and "hãy" in d["loi_goc"] for d in rep["khac_biet"]))
        ts = [w["s"] for s in new for w in s["words"]]
        self.assertEqual(ts, sorted(ts))

    def test_prompt_ngan(self):
        p = tu_dien.whisper_prompt(tu_dien.LINH_VUC, "Kendy Huyền Học.")
        self.assertLessEqual(len(p), 420)
        self.assertIn("Kendy", p)


class TestBoCuc(unittest.TestCase):
    def test_tranh_mat_va_phu_de(self):
        face = [(t, [bo_cuc.Box(380, 700, 320, 400)]) for t in (0, 0.5, 1, 1.5, 2)]
        hard, soft = bo_cuc.obstacles_in(face, 0, 2, [], [bo_cuc.subtitle_band()], tranh_tay=False)
        box, ok = bo_cuc.choose(bo_cuc.card_candidates(400, 690), hard, soft)
        self.assertTrue(ok)
        self.assertFalse(any(box.hits(o) for o in hard + soft))
        # bật vùng tay: không bao giờ che mặt (vùng cấm), dù có thể phải chạm vùng tay
        hard, soft = bo_cuc.obstacles_in(face, 0, 2, [], [bo_cuc.subtitle_band()], tranh_tay=True)
        box, _ = bo_cuc.choose(bo_cuc.card_candidates(400, 690), hard, soft)
        self.assertFalse(any(box.hits(o) for o in hard))
        self.assertGreaterEqual(box.y, bo_cuc.SAFE_TOP)
        self.assertLessEqual(box.x + box.w, bo_cuc.OUT_W - bo_cuc.SAFE_RIGHT + 1)

    def test_geometry_cat(self):
        g = bo_cuc.geometry("cat", 1920, 1080, (606, 1078, 1200, 1))
        b = g.map(bo_cuc.Box(1200, 1, 606, 1078))
        self.assertAlmostEqual(b.x, 0, places=3)
        self.assertAlmostEqual(b.w, 1080, places=3)

    def test_preset_kendy(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps({"phong_cach": "kendy", "video": "x.mp4", "xuat": {"net": "nhe"}}), "utf-8")
            cfg = kvt.load_config(p)
            self.assertEqual(cfg["xuat"]["mau"], "kendy")
            self.assertEqual(cfg["xuat"]["net"], "nhe")  # cấu hình dự án ghi đè phong cách
            self.assertEqual(cfg["phu_de_tham_so"]["kieu"], "kendy")
            self.assertIsNone(cfg["intro"])  # intro/outro không bắt buộc


class TestTichHopMoRong(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.d = d
        cls.src = d / "src.mp4"
        ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=8", "-f", "lavfi", "-i",
           "aevalsrc='(lt(t,2)+gte(t,4.5))*0.3*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*3*t))+0.0005*random(0)':s=48000:d=8",
           "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(cls.src))
        cls.card = d / "card.png"
        ff("-f", "lavfi", "-i", "testsrc=s=600x1036:d=1", "-frames:v", "1", str(cls.card))
        cls.voice = d / "voice.mp3"
        ff("-f", "lavfi", "-i", "sine=f=300:d=6", "-af", "volume=0.3", "-ar", "48000", str(cls.voice))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_cat_lang_chuyen_mo(self):
        out = self.d / "cut_xf.mp4"
        self.assertEqual(kvt.main(["cat-lang", str(self.src), "-o", str(out), "--chuyen-mo", "0.1",
                                   "--che-do", "am-luong"]), 0)
        info = kvt.probe(out)
        v = float(kvt.stream(info, "video")["duration"])
        a = float(kvt.stream(info, "audio")["duration"])
        self.assertLess(abs(v - a), 0.05)
        rep = json.loads(out.with_suffix(".cat-lang.json").read_text("utf-8"))
        self.assertEqual(len(rep["chuyen_mo_giay"]), 1)

    def test_cat_lang_tep_am_thanh(self):
        wav = self.d / "a.wav"
        ff("-i", str(self.src), "-vn", str(wav))
        out = self.d / "a_cut.wav"
        self.assertEqual(kvt.main(["cat-lang", str(wav), "-o", str(out)]), 0)
        self.assertLess(kvt.duration_of(kvt.probe(out)), 7.0)

    def test_ghep_canh_anh_video_long_tieng(self):
        out = self.d / "canh.mp4"
        rc = kvt.main(["ghep-canh", f"{self.card}", f"{self.src}@0-2", "-o", str(out), "--long-tieng", str(self.voice)])
        self.assertEqual(rc, 0)
        info = kvt.probe(out)
        v = kvt.stream(info, "video")
        self.assertEqual((int(v["width"]), int(v["height"])), (1080, 1920))
        self.assertAlmostEqual(kvt.duration_of(info), 6.0, delta=0.15)  # theo độ dài lồng tiếng

    def test_xuat_kendy_la_bai_diem_nhan_cta(self):
        out = self.d / "kendy.mp4"
        rc = kvt.main(["xuat", str(self.src), "-o", str(out), "--preset", "ultrafast", "--khung", "auto",
                       "--mau", "kendy", "--net", "vua", "--la-bai", f"{self.card}@1-3", "--vien-la-bai", "#D8BE8C",
                       "--diem-nhan", "Lá bài chủ đạo|Mặt Trăng@3.5-5", "--cta", "Theo dõi Kendy Huyền Học|Thông điệp mỗi ngày",
                       "--vung-tranh", "330,500,420,700@0-8"])
        self.assertEqual(rc, 0)
        layout = json.loads(out.with_suffix(".bo-cuc.json").read_text("utf-8"))
        self.assertEqual(layout["khung"], "nen-mo")  # video ngang, không có mặt → giữ trọn khung
        kinds = [m["loai"] for m in layout["muc"]]
        self.assertEqual(kinds, ["la_bai", "diem_nhan", "cta"])
        card = layout["muc"][0]
        zone = bo_cuc.Box(330, 500, 420, 700)
        self.assertFalse(bo_cuc.Box(card["x"], card["y"], card["rong"], card["cao"]).hits(zone))
        # khung hình có lá bài: vùng lá bài khác hẳn khung không có
        a, b = self.d / "f1.png", self.d / "f2.png"
        ff("-ss", "2", "-i", str(out), "-frames:v", "1", str(a))
        ff("-ss", "0.2", "-i", str(out), "-frames:v", "1", str(b))
        self.assertNotEqual(a.read_bytes(), b.read_bytes())

    @unittest.skipIf(os.environ.get("KVT_BO_QUA_MOTION"), "bỏ qua motion")
    def test_motion_intro_outro(self):
        i = self.d / "intro.mp4"
        o = self.d / "outro.mp4"
        self.assertEqual(kvt.main(["intro", "-o", str(i), "--anh", str(self.card), "--tieu-de", "THÔNG ĐIỆP"]), 0)
        self.assertEqual(kvt.main(["outro", "-o", str(o), "--loi-moi", "Theo dõi để nhận thông điệp"]), 0)
        for p in (i, o):
            v = kvt.stream(kvt.probe(p), "video")
            self.assertEqual((int(v["width"]), int(v["height"])), (1080, 1920))


class TestKhongDuongDanCoDinh(unittest.TestCase):
    def test_khong_co_duong_dan_may_ao(self):
        bad = []
        for p in ROOT.rglob("*"):
            if any(x in p.parts for x in (".venv", "node_modules", ".cache", "test-media", "test-out", ".git",
                                          ".hyperframes")) or not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".js", ".jsx", ".json", ".md", ".sh", ".html", ""}:
                continue
            if p.name in ("test_mo_rong.py", ".chrome-path"):  # .chrome-path: riêng từng máy, không lưu lên kho
                continue
            t = p.read_text("utf-8", errors="ignore")
            if "/home/user" in t or "/tmp/claude" in t or "/opt/pw-browsers/chromium_headless_shell-1243" in t:
                bad.append(str(p.relative_to(ROOT)))
        self.assertEqual(bad, [], f"Có đường dẫn cố định của máy ảo: {bad}")


if __name__ == "__main__":
    unittest.main()


class TestTaiLieu(unittest.TestCase):
    def test_skill_tong_dong_bo(self):
        self.assertEqual((ROOT / "SKILL.md").read_text("utf-8"),
                         (ROOT / ".claude" / "skills" / "kendy-video" / "SKILL.md").read_text("utf-8"))

    def test_du_9_skill_co_frontmatter(self):
        names = sorted(p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(names), 9, names)
        for n in names:
            t = (ROOT / ".claude" / "skills" / n / "SKILL.md").read_text("utf-8")
            self.assertTrue(t.startswith("---\nname: "), n)
            self.assertIn("description:", t.split("---")[1])

    def test_vi_du_hop_le(self):
        for p in (ROOT / "vi-du").glob("*.json"):
            cfg = kvt.load_config(p)
            self.assertTrue(cfg.get("video") or cfg.get("canh"), p.name)
