"""Dựng motion graphics bằng Remotion / HyperFrames từ dòng lệnh – không cần nhớ đường dẫn trình duyệt.

Mỗi lần dựng sao chép bản mẫu sang thư mục tạm, chèn ảnh/chữ của Kendy, dựng cục bộ, rồi xoá thư mục tạm.
Không gọi dịch vụ HeyGen / HyperFrames publish (có thể tính phí)."""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "motion" / "remotion"
HYPER = ROOT / "motion" / "hyperframes-outro"
FONTS = ROOT / "assets" / "fonts"
BIN = ROOT / "node_modules" / ".bin"


def find_chrome() -> str | None:
    """Tìm trình duyệt Chrome/Chromium headless: biến KVT_CHROME → .chrome-path → vị trí thường gặp."""
    env = os.environ.get("KVT_CHROME")
    if env and Path(env).is_file():
        return env
    cp = ROOT / ".chrome-path"
    if cp.is_file():
        p = cp.read_text().strip()
        if p and Path(p).is_file():
            return p
    cands = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    cands += sorted(glob.glob(str(Path.home() / ".cache/ms-playwright/chromium_headless_shell-*/chrome-*/chrome-headless-shell")))
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        w = shutil.which(name)
        if w:
            cands.append(w)
    for mac in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",):
        cands.append(mac)
    for c in cands:
        if Path(c).is_file():
            return c
    return None  # Remotion sẽ tự tải Chrome Headless Shell (miễn phí) nếu không có


def _env() -> dict:
    e = dict(os.environ)
    e.update({"REMOTION_DISABLE_TELEMETRY": "1", "HYPERFRAMES_NO_TELEMETRY": "1", "HYPERFRAMES_SKIP_SKILLS": "1"})
    return e


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    p = subprocess.run(cmd, cwd=cwd, env=_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError("Dựng motion thất bại:\n" + "\n".join(p.stdout.splitlines()[-25:]))


def remotion(comp: str, out: str, props: dict, image: str | None) -> str:
    if not (BIN / "remotion").exists():
        raise RuntimeError("Chưa cài Remotion – chạy ./cai-dat.sh")
    with tempfile.TemporaryDirectory(prefix="kvt-rm-") as tmp:
        pub = Path(tmp) / "public"
        shutil.copytree(REMOTION / "public", pub)
        if image:
            src = Path(image)
            if not src.is_file():
                raise RuntimeError(f"Không thấy ảnh: {image}")
            name = "anh-nguoi-dung" + src.suffix.lower()
            shutil.copy(src, pub / name)
            props = {**props, "anhLaBai": name}
        cmd = [str(BIN / "remotion"), "render", str(REMOTION / "src" / "index.jsx"), comp, str(Path(out).resolve()),
               f"--public-dir={pub}", "--crf=16", "--log=error", f"--props={json.dumps(props, ensure_ascii=False)}"]
        chrome = find_chrome()
        if chrome:
            cmd.append(f"--browser-executable={chrome}")
        _run(cmd, cwd=ROOT)
    return out


def hyperframes_outro(out: str, variables: dict, image: str | None) -> str:
    if not (BIN / "hyperframes").exists():
        raise RuntimeError("Chưa cài HyperFrames – chạy ./cai-dat.sh")
    with tempfile.TemporaryDirectory(prefix="kvt-hf-") as tmp:
        proj = Path(tmp) / "outro"
        shutil.copytree(HYPER, proj, ignore=shutil.ignore_patterns(".hyperframes", "renders"))
        if image:
            src = Path(image)
            if not src.is_file():
                raise RuntimeError(f"Không thấy ảnh: {image}")
            shutil.copy(src, proj / "assets" / ("anh-nguoi-dung" + src.suffix.lower()))
            variables = {**variables, "anhLaBai": "assets/anh-nguoi-dung" + src.suffix.lower()}
        _run([str(BIN / "hyperframes"), "render", "-o", str(Path(out).resolve()), "--quality", "delivery", "--quiet",
              "--no-browser-gpu", "--variables", json.dumps(variables, ensure_ascii=False)], cwd=proj)
    return out
