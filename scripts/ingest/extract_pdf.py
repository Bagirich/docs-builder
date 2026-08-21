"""Чужой PDF -> ingest/raw.txt (текст по страницам через pdfplumber).

Если извлекаемого текста почти нет — печатает предупреждение: презентация
картиночная, её должен прочитать субагент source-extractor визуально.

Использование: python scripts/ingest/extract_pdf.py <file.pdf>
"""
import os
import sys
import pdfplumber

OUT = "ingest/raw.txt"


def main(pdf_path):
    os.makedirs("ingest", exist_ok=True)
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            chunks.append(f"## Страница {i}\n\n{text}")
    full = "\n\n".join(chunks)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(full)

    stripped = full.replace("#", "").replace("Страница", "").strip()
    if len(stripped) < 200:
        print(
            "ВНИМАНИЕ: текста почти нет — презентация, видимо, картиночная. "
            "Субагент должен прочитать страницы PDF визуально."
        )
    print(f"Извлечено {len(full)} символов -> {OUT}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Укажите путь к PDF")
    main(sys.argv[1])
