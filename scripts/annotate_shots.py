"""Аннотация скринов для гайда: маскировка секретов + бордовые номерные рамки «куда жать».
Координаты — ФРАКЦИОННЫЕ (0..1) от размера картинки, чтобы не зависеть от разрешения.

Использование: правим SPEC ниже и запускаем .venv/bin/python scripts/annotate_shots.py
Вход: input/px6/r1, input/dolphin/r1, input/dolphin/user · Выход: assets/guide-shots/
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path("assets/guide-shots"); OUT.mkdir(parents=True, exist_ok=True)

BURG = (139, 21, 38)       # бордовый
BURG2 = (183, 28, 28)
GOLD = (201, 162, 39)
DARK = (26, 29, 34)

def font(sz, bold=True):
    paths = [
        "assets/fonts/Montserrat-Bold.ttf" if bold else "assets/fonts/Montserrat-Regular.ttf",
        "assets/fonts/OpenSans-Bold.ttf" if bold else "assets/fonts/OpenSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in paths:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()

def px(img, box):
    W, H = img.size
    x0, y0, x1, y1 = box
    return [int(x0*W), int(y0*H), int(x1*W), int(y1*H)]

def mask(draw, img, box, label="• • •"):
    x0, y0, x1, y1 = px(img, box)
    bw, bh = x1-x0, y1-y0
    r = max(6, bh//6)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=DARK, outline=GOLD, width=max(2, bh//28))
    if label:
        # подобрать размер так, чтобы подпись влезла и по высоте, и по ширине
        sz = max(12, bh//3)
        f = font(sz, bold=True)
        while sz > 11:
            tb = draw.textbbox((0,0), label, font=f)
            if (tb[2]-tb[0]) <= bw-18 and (tb[3]-tb[1]) <= bh-8:
                break
            sz -= 2; f = font(sz, bold=True)
        tb = draw.textbbox((0,0), label, font=f)
        tw, th = tb[2]-tb[0], tb[3]-tb[1]
        draw.text((x0+(bw-tw)/2, y0+(bh-th)/2 - tb[1]), label, fill=(235,235,235), font=f)

def frame(draw, img, box, num, label=None):
    x0, y0, x1, y1 = px(img, box)
    W, H = img.size
    w = max(3, int(W*0.0028))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=max(8, w*3), outline=BURG, width=w)
    # номерной бейдж в левом верхнем углу рамки
    rad = max(16, int(W*0.014))
    cx, cy = x0, y0
    draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], fill=BURG, outline=(255,255,255), width=max(2,w//2))
    f = font(int(rad*1.2), bold=True)
    s = str(num)
    tb = draw.textbbox((0,0), s, font=f); tw, th = tb[2]-tb[0], tb[3]-tb[1]
    draw.text((cx-tw/2, cy-th/2 - tb[1]), s, fill=(255,255,255), font=f)
    if label:
        f2 = font(max(13, int(W*0.012)), bold=True)
        ly = y1 + max(4, int(H*0.006))
        tb = draw.textbbox((0,0), label, font=f2)
        draw.rectangle([x0, ly, x0+(tb[2]-tb[0])+12, ly+(tb[3]-tb[1])+10], fill=BURG)
        draw.text((x0+6, ly+4), label, fill=(255,255,255), font=f2)

def process(src, dst, masks=None, frames=None):
    p = pathlib.Path(src)
    if not p.exists():
        print(f"!! нет файла {src}"); return
    img = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(img)
    for m in (masks or []):
        mask(d, img, m.get("box"), m.get("label", "• • •"))
    for fr in (frames or []):
        frame(d, img, fr["box"], fr["num"], fr.get("label"))
    img.save(OUT/dst)
    print(f">>> {dst}  ({img.size[0]}x{img.size[1]})")

# ============ SPEC: только маскировка (рамки добавим вторым проходом) ============
JOBS = [
    # Dolphin: список профилей (новый профиль + START) — маскируем колонку Proxy и e-mail внизу
    dict(src="input/dolphin/user/u8_profiles_list_new.png", dst="d_list_start.png",
         masks=[{"box":(0.862,0.27,1.0,0.45),"label":"прокси"},
                {"box":(0.83,0.965,1.0,1.0),"label":"e-mail"}]),
    # Dolphin: профиль запущен (STOP) — то же
    dict(src="input/dolphin/user/u9_profile_running_stop.png", dst="d_running_stop.png",
         masks=[{"box":(0.862,0.27,1.0,0.45),"label":"прокси"},
                {"box":(0.83,0.965,1.0,1.0),"label":"e-mail"}]),
    # Dolphin: форма с прокси + зелёная проверка — маскируем строку прокси и SUMMARY-proxy
    dict(src="input/dolphin/user/u7_proxy_filled_check.png", dst="d_proxy_filled.png",
         masks=[{"box":(0.135,0.455,0.52,0.505),"label":"socks5://••••:••••@••••:••••"},
                {"box":(0.625,0.442,0.815,0.515),"label":"скрыто"},
                {"box":(0.86,0.155,1.0,0.27),"label":""}]),
    # Dolphin: «Suspicious Attempt» — маскируем код из письма
    dict(src="input/dolphin/user/u3_suspicious_code.png", dst="d_suspicious.png",
         masks=[{"box":(0.305,0.445,0.62,0.505),"label":"код из письма"}]),
    # Dolphin: запущенный браузер (Google new tab) — справа виден список прокси
    dict(src="input/dolphin/user/u10_browser_google.png", dst="d_browser.png",
         masks=[{"box":(0.86,0.21,1.0,0.46),"label":"прокси"}]),
    # Dolphin: Gemini открыт — чистый, секретов нет (оставляем как есть, просто копия)
    dict(src="input/dolphin/user/u11_gemini_open.png", dst="d_gemini.png"),
    # px6: Мои прокси — маскируем колонку с IP/логином/паролем
    dict(src="input/px6/r1/22_my_proxies.png", dst="p_my_proxies.png",
         masks=[{"box":(0.285,0.275,0.63,0.42),"label":"IP : порт : логин : пароль"}]),
]

for j in JOBS:
    process(j["src"], j["dst"], j.get("masks"), j.get("frames"))
print("DONE masks")

# ============ ВТОРОЙ КОНВЕЙЕР: crop + доп.маски + номерные рамки ============
# Читает УЖЕ ЗАМАСКИРОВАННЫЕ скрины из assets/guide-shots/, кадрирует под читаемость,
# домаскировывает приватность (IP-host/e-mail), ставит бордовые номерные рамки.
# Выход: assets/guide-shots/ann/<name>.png . Идемпотентно (всегда из оригинала guide-shots).
ANN = OUT / "ann"; ANN.mkdir(parents=True, exist_ok=True)

def process2(name, crop=None, masks=None, frames=None):
    src = OUT / name
    if not src.exists():
        print(f"!! нет {src}"); return
    img = Image.open(src).convert("RGB")
    if crop:
        W, H = img.size
        x0, y0, x1, y1 = crop
        img = img.crop((int(x0*W), int(y0*H), int(x1*W), int(y1*H)))
    d = ImageDraw.Draw(img)
    for m in (masks or []):
        mask(d, img, m["box"], m.get("label", "• • •"))
    for fr in (frames or []):
        frame(d, img, fr["box"], fr["num"], fr.get("label"))
    img.save(ANN / name)
    print(f">>> ann/{name}  ({img.size[0]}x{img.size[1]})")

# crop — фракции исходника; masks/frames — фракции УЖЕ КАДРИРОВАННОГО изображения.
# frames: num = номер шага в легенде HTML; подписи НЕ печатаем на скрине (легенда в вёрстке).
ANNJOBS = [
    dict(name="p_register.png", crop=(0.30, 0.085, 0.70, 0.255),
         frames=[{"num": 1, "box": (0.19, 0.195, 0.80, 0.290)},   # E-mail
                 {"num": 2, "box": (0.19, 0.310, 0.80, 0.400)},   # Пароль
                 {"num": 3, "box": (0.195, 0.420, 0.275, 0.475)}, # галочка согласия
                 {"num": 4, "box": (0.19, 0.500, 0.59, 0.660)},   # код с картинки
                 {"num": 5, "box": (0.19, 0.665, 0.80, 0.745)}]), # Регистрация
    dict(name="p_payment.png", crop=(0.00, 0.060, 1.00, 0.700),
         frames=[{"num": 1, "box": (0.110, 0.150, 0.260, 0.228)}, # Баланс → Пополнение
                 {"num": 2, "box": (0.330, 0.650, 0.448, 0.835)}, # Card (RUS/World)
                 {"num": 3, "box": (0.302, 0.850, 0.497, 0.915)}, # Сумма 120
                 {"num": 4, "box": (0.497, 0.850, 0.568, 0.915)}]), # Продолжить
    dict(name="p_order.png", crop=(0.00, 0.085, 1.00, 0.490),
         frames=[{"num": 1, "box": (0.515, 0.115, 0.945, 0.205)}, # карточка IPv4 (заголовок)
                 {"num": 2, "box": (0.550, 0.265, 0.945, 0.350)}, # СТРАНА
                 {"num": 3, "box": (0.550, 0.355, 0.715, 0.435)}, # КОЛ-ВО
                 {"num": 4, "box": (0.740, 0.355, 0.945, 0.435)}, # ПЕРИОД
                 {"num": 5, "box": (0.515, 0.475, 0.945, 0.555)}]), # Купить
    dict(name="p_order_country.png", crop=(0.00, 0.085, 1.00, 0.490)),  # запас (список стран)
    dict(name="p_my_proxies.png", crop=(0.00, 0.075, 1.00, 0.520),
         frames=[{"num": 1, "box": (0.265, 0.435, 0.585, 0.715)}, # строка прокси (4 значения)
                 {"num": 2, "box": (0.835, 0.520, 0.885, 0.730)}, # показать/копировать
                 {"num": 3, "box": (0.658, 0.335, 0.718, 0.405)}]), # Экспорт
    dict(name="d_download.png", crop=(0.00, 0.000, 1.00, 0.845),
         frames=[{"num": 1, "box": (0.170, 0.555, 0.360, 0.615)}, # Windows
                 {"num": 2, "box": (0.410, 0.555, 0.595, 0.615)}, # macOS
                 {"num": 3, "box": (0.650, 0.555, 0.875, 0.615)}]), # Linux
    dict(name="d_register.png", crop=(0.28, 0.040, 0.72, 0.900),
         frames=[{"num": 1, "box": (0.180, 0.295, 0.810, 0.355)}, # Email
                 {"num": 2, "box": (0.180, 0.435, 0.810, 0.490)}, # Password
                 {"num": 3, "box": (0.180, 0.530, 0.810, 0.585)}, # WhatsApp/мессенджер
                 {"num": 4, "box": (0.175, 0.825, 0.255, 0.875)}, # галочка согласия
                 {"num": 5, "box": (0.180, 0.895, 0.810, 0.965)}]), # Create an account
    dict(name="d_suspicious.png", crop=(0.27, 0.050, 0.73, 0.600),
         frames=[{"num": 1, "box": (0.065, 0.695, 0.595, 0.820)}, # код из письма
                 {"num": 2, "box": (0.805, 0.710, 0.915, 0.800)}]), # Confirm
    dict(name="d_proxy_filled.png", crop=None,
         masks=[{"box": (0.123, 0.493, 0.196, 0.528), "label": ""},   # IP-host в зелёной проверке
                {"box": (0.600, 0.395, 0.935, 0.520), "label": "скрыто"},  # строка Proxy в сводке
                {"box": (0.860, 0.270, 1.000, 0.345), "label": ""},   # остаток под золотой плашкой
                {"box": (0.80, 0.95, 1.00, 1.00), "label": ""}],      # e-mail в статус-баре
         frames=[{"num": 1, "box": (0.205, 0.345, 0.275, 0.385)},  # New proxy
                 {"num": 2, "box": (0.218, 0.390, 0.272, 0.430)},  # SOCKS5
                 {"num": 3, "box": (0.130, 0.440, 0.550, 0.505)},  # строка данных прокси
                 {"num": 4, "box": (0.115, 0.505, 0.430, 0.545)},  # зелёная проверка England/London
                 {"num": 5, "box": (0.735, 0.845, 0.870, 0.895)}]), # CREATE PROFILE
    dict(name="d_list_start.png", crop=None,
         frames=[{"num": 1, "box": (0.342, 0.260, 0.450, 0.300)}]), # START (Gemini UK)
    dict(name="d_running_stop.png", crop=None,
         frames=[{"num": 1, "box": (0.365, 0.260, 0.473, 0.300)}]), # STOP (Gemini UK, со сдвигом из-за иконки)
    dict(name="d_browser.png", crop=None,
         masks=[{"box": (0.80, 0.95, 1.00, 1.00), "label": ""}],      # e-mail в статус-баре
         frames=[{"num": 1, "box": (0.085, 0.078, 0.158, 0.122)}]),  # ярлык профиля Gemini UK
    dict(name="t_2ip.png", crop=(0.00, 0.00, 1.00, 0.78),
         masks=[{"box": (0.025, 0.255, 0.215, 0.400), "label": "IP скрыт"}],  # крупный IP-host
         frames=[{"num": 1, "box": (0.615, 0.495, 0.905, 0.555)},   # местоположение (зарубежное)
                 {"num": 2, "box": (0.615, 0.685, 0.905, 0.745)}]), # Прокси: не используется
    dict(name="d_gemini.png", crop=None,
         frames=[{"num": 1, "box": (0.300, 0.550, 0.720, 0.610)},   # Ask Gemini
                 {"num": 2, "box": (0.945, 0.130, 1.000, 0.175)}]), # Sign in
]

for j in ANNJOBS:
    process2(j["name"], j.get("crop"), j.get("masks"), j.get("frames"))
print("DONE ann")
