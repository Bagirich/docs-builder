"""Визуальный QA по НАСТОЯЩЕМУ PDF (а не по HTML).

Рендерит каждую страницу output/output.pdf в PNG (qa/pageNN.png) через Quartz —
тот же движок, что и macOS Preview. Это принципиально: Quartz рисует box-shadow,
прозрачности и градиенты так же, как их увидит человек, а pypdfium2/PDFium тени
НЕ рисует и маскирует дефекты вроде тёмной «подложки» за карточками.

Бонус: печатает метрику заполнения каждой страницы (до какой доли высоты доходит
непустой контент, без зоны подвала) и помечает ⚠ светлые страницы, заполненные
менее чем на 75% — ловит вторую частую беду (пустой низ листа). Заодно меряет
самый длинный пустой промежуток ВНУТРИ контента: дыра посреди страницы читается
как поломка вёрстки, а не как воздух.

Тёмные страницы автоматика не гейтит намеренно — обложка и цитата воздушны по
замыслу; их метрика печатается, смотреть глазами.

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
HOLE_MAX = 0.22          # какой пустой промежуток внутри контента уже читается как дыра
EDGE_MAX = 0.985         # контент ниже подвала = страница переполнена и лишнее обрезано
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
    """Куда доходит контент и нет ли дыры посередине.

    Возвращает (fill, is_dark, hole, край): доля высоты до последней строки с контентом,
    тёмная ли страница, самый длинный пустой промежуток ВНУТРИ контента и то,
    куда контент доходит по всей высоте листа (признак переполнения).

    Фон берём по каждой строке отдельно (медиана строки), а не по верхней строке:
    у тёмных страниц фон — вертикальный градиент, и при сравнении с одной верхней
    строкой весь низ считался «контентом». Из-за этого тёмные всегда показывали
    85–92%, а настоящий разрыв на такой странице проходил проверку незамеченным.
    """
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return None, None, None, None
    a = np.asarray(Image.open(png_path).convert("RGB")).astype(int)
    H = a.shape[0]
    is_dark = a[2].mean() < 110
    фон_строки = np.median(a, axis=1, keepdims=True)
    diff = (np.abs(a - фон_строки).sum(axis=2) > 40).mean(axis=1)
    rows = np.where(diff[: int(H * FOOTER_ZONE)] > 0.02)[0]
    # отдельно — по ВСЕЙ высоте: у нормальной страницы контент кончается подвалом
    # (~0.97), а если текст ушёл ниже подвала, значит он не поместился и обрезан
    все_строки = np.where(diff > 0.02)[0]
    край = (все_строки.max() + 1) / H if len(все_строки) else 0.0
    if not len(rows):
        return 0.0, is_dark, 0.0, край
    разрывы = np.diff(rows)
    дыра = (разрывы.max() - 1) / H if len(разрывы) else 0.0
    return (rows.max() + 1) / H, is_dark, max(дыра, 0.0), край


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
            fill, is_dark, hole, край = fill_ratio(dst)
            if fill is None:
                print(f"page{i + 1:02d}: ок (метрика недоступна — нет numpy/PIL)")
                continue
            tag = "тёмная" if is_dark else "светлая"
            flag = ""
            if not is_dark and fill < FILL_MIN:
                flag = "  ⚠ ПУСТОЙ НИЗ (заполни ≥2/3)"
                warned.append(i + 1)
            elif край > EDGE_MAX:
                flag = "  ⚠ КОНТЕНТ УПИРАЕТСЯ В КРАЙ (страница не продолжается — лишнее обрезано)"
                warned.append(i + 1)
            elif not is_dark and hole > HOLE_MAX:
                flag = f"  ⚠ ДЫРА ПОСЕРЕДИНЕ ({hole:.0%} высоты пусто)"
                warned.append(i + 1)
            дыра = f", дыра {hole:.0%}" if hole > 0.05 else ""
            print(f"page{i + 1:02d}: {tag}, заполнение {fill:.0%}{дыра}{flag}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{n} страниц -> {OUT}/page*.png (Quartz)")
    if warned:
        print(f"⚠ Страницы с замечаниями: {warned} — смотри пометки выше, чини и пере-рендери.")
    else:
        print("✓ Светлые страницы заполнены. Тёмные автоматика НЕ гейтит —")
        print("  на обложке и цитате воздух уместен. Посмотрите их PNG глазами.")


if __name__ == "__main__":
    main()
