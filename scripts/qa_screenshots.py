"""Визуальный QA по НАСТОЯЩЕМУ PDF (а не по HTML).

Рендерит каждую страницу output/output.pdf в PNG (qa/pageNN.png) через Quartz —
тот же движок, что и macOS Preview. Это принципиально: Quartz рисует box-shadow,
прозрачности и градиенты так же, как их увидит человек, а pypdfium2/PDFium тени
НЕ рисует и маскирует дефекты вроде тёмной «подложки» за карточками.

Бонус: печатает метрику заполнения каждой страницы (до какой доли высоты доходит
непустой контент, без зоны подвала) и помечает ⚠ светлые страницы, заполненные
менее чем на 75% — ловит вторую частую беду (пустой низ листа).

Использование: .venv/bin/python scripts/qa_screenshots.py [путь_к.pdf]
Требует macOS (sips). pypdf + Pillow + numpy уже в окружении.
"""
import os
import sys
import shutil
import tempfile
import subprocess

from pypdf import PdfReader, PdfWriter

PDF = sys.argv[1] if len(sys.argv) > 1 else "output/output.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "qa"
FILL_MIN = 0.75          # порог заполнения для светлых страниц
FOOTER_ZONE = 0.92       # нижние 8% — зона подвала, не считаем за контент
MAX_DIM = 1400           # макс. сторона PNG (для лёгких файлов)


def quartz_png(src_pdf: str, dst_png: str) -> bool:
    """PDF (1 стр.) -> PNG через sips (Quartz). True при успехе."""
    r = subprocess.run(
        ["sips", "-s", "format", "png",
         "-Z", str(MAX_DIM), src_pdf, "--out", dst_png],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0 and os.path.exists(dst_png)


def fill_ratio(png_path: str):
    """Доля высоты, до которой доходит непустой контент (без зоны подвала).
    Возвращает (fill, is_dark). Фон = цвет верхней строки пикселей."""
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return None, None
    a = np.asarray(Image.open(png_path).convert("RGB")).astype(int)
    H = a.shape[0]
    bg = a[2].mean(axis=0)
    is_dark = bg.mean() < 110
    diff = (np.abs(a - bg).sum(axis=2) > 40).mean(axis=1)
    rows = np.where(diff[: int(H * FOOTER_ZONE)] > 0.02)[0]
    return ((rows.max() + 1) / H if len(rows) else 0.0), is_dark


def main():
    if not os.path.exists(PDF):
        sys.exit(f"❌ Нет файла {PDF}. Сначала запусти scripts/render.py.")
    os.makedirs(OUT, exist_ok=True)
    reader = PdfReader(PDF)
    n = len(reader.pages)
    tmp = tempfile.mkdtemp(prefix="qa_pdf_")
    warned = []
    try:
        for i in range(n):
            one = os.path.join(tmp, f"p{i + 1:02d}.pdf")
            w = PdfWriter()
            w.add_page(reader.pages[i])
            with open(one, "wb") as f:
                w.write(f)
            dst = f"{OUT}/page{i + 1:02d}.png"
            if not quartz_png(one, dst):
                print(f"page{i + 1:02d}: ⚠ sips не отрендерил")
                continue
            fill, is_dark = fill_ratio(dst)
            if fill is None:
                print(f"page{i + 1:02d}: ок (метрика недоступна — нет numpy/PIL)")
                continue
            tag = "тёмная" if is_dark else "светлая"
            flag = ""
            if not is_dark and fill < FILL_MIN:
                flag = "  ⚠ ПУСТОЙ НИЗ (заполни ≥2/3)"
                warned.append(i + 1)
            print(f"page{i + 1:02d}: {tag}, заполнение {fill:.0%}{flag}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{n} страниц -> {OUT}/page*.png (Quartz)")
    if warned:
        print(f"⚠ Недозаполненные светлые страницы: {warned} — доработай и пере-рендери.")
    else:
        print("✓ Все светлые страницы заполнены, тёмные подложки видны глазами на PNG.")


if __name__ == "__main__":
    main()
