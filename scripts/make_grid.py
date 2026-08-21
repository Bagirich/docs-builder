"""Сделать превью скринов с координатной сеткой в ДОЛЯХ (0.0–1.0) — чтобы точно снять
координаты элементов для рамок/замазки. Превью кладём в qa-covers/grid/.

Запуск: .venv/bin/python scripts/make_grid.py
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

SRC = pathlib.Path("input/aistudio/r1")
OUT = pathlib.Path("qa-covers/grid"); OUT.mkdir(parents=True, exist_ok=True)
FONT = "assets/fonts/Montserrat.ttf"

IMAGES = [
    ("11_apikey_loaded_full.png", "A_keys_banner"),
    ("80_aistudio_after_full.png", "B_keys_clean"),
    ("20_secure_dialog_full.png", "C_secure_dialog"),
    ("40_gcloud_credentials_full.png", "D_console_before"),
    ("60_key_editor_before_full.png", "E_editor_before"),
    ("63_ready_to_save_full.png", "F_ready_to_save"),
    ("71_creds_after_full.png", "G_console_after"),
]

PREVIEW_W = 1280

for src, name in IMAGES:
    p = SRC / src
    if not p.exists():
        print("нет файла:", p); continue
    im = Image.open(p).convert("RGB")
    W, H = im.size
    scale = PREVIEW_W / W
    pw, ph = PREVIEW_W, int(H * scale)
    pv = im.resize((pw, ph))
    d = ImageDraw.Draw(pv)
    try:
        f = ImageFont.truetype(FONT, 16)
    except Exception:
        f = ImageFont.load_default()
    # вертикальные линии каждые 0.05, подписи каждые 0.1
    for i in range(0, 21):
        frac = i / 20
        x = int(frac * pw)
        col = (220, 30, 60) if i % 2 == 0 else (180, 180, 180)
        d.line([(x, 0), (x, ph)], fill=col, width=1)
        if i % 2 == 0:
            d.text((x + 2, 2), f"{frac:.1f}", fill=(200, 0, 40), font=f)
    for i in range(0, 21):
        frac = i / 20
        y = int(frac * ph)
        col = (220, 30, 60) if i % 2 == 0 else (180, 180, 180)
        d.line([(0, y), (pw, y)], fill=col, width=1)
        if i % 2 == 0:
            d.text((2, y + 1), f"{frac:.1f}", fill=(200, 0, 40), font=f)
    pv.save(OUT / f"{name}.png")
    print("сохранил", OUT / f"{name}.png", "из", src, f"({W}x{H})")
print("DONE")
