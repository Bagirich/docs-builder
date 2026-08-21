"""QA: подсчёт кликабельных ссылок-аннотаций (/Link с /URI) в PDF.

Использование: python scripts/check_links.py [output/output.pdf]
"""
import sys
from pypdf import PdfReader


def count_links(pdf_path):
    reader = PdfReader(pdf_path)
    n = 0
    for page in reader.pages:
        if "/Annots" not in page:
            continue
        for a in page["/Annots"]:
            obj = a.get_object()
            if obj.get("/Subtype") == "/Link" and obj.get("/A", {}).get("/URI"):
                n += 1
    return n


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "output/output.pdf"
    print(f"Кликабельных ссылок: {count_links(path)}")
