"""ingest/raw.txt -> ingest/normalized.md.

Базовая нормализация: схлопывает лишние пустые строки и хвостовые пробелы.
Тонкую структуру (заголовки, списки, ссылки) досверяет субагент source-extractor.
"""
import re

SRC = "ingest/raw.txt"
OUT = "ingest/normalized.md"


def normalize(text):
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)   # хвостовые пробелы
    text = re.sub(r"\n{3,}", "\n\n", text)   # не больше одной пустой строки подряд
    return text.strip() + "\n"


def main():
    with open(SRC, encoding="utf-8") as f:
        raw = f.read()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(normalize(raw))
    print(f"Нормализовано -> {OUT}")


if __name__ == "__main__":
    main()
