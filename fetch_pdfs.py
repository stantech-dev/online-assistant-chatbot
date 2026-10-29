"""Fetches pdfs from the website but not automatically ingested """
from pathlib import Path

from pypdf import PdfReader

from polite import polite_get
import logging

logging.getLogger("pypdf").setLevel(logging.ERROR)

BASE = "https://au.ac.ke/wp-content/uploads/"
# name: (url, keyword to look for in the text)
SOURCES = {
    "fee-structure-24-25.pdf": (BASE + "2025/07/FEE-STRUCTURE-AU-24-25.pdf", "PSYCHOLOGY"),
    "accommodation-2026-27.pdf": (BASE + "2026/08/AU_05082026_STUDENTS-ACCOMODATION-2027-Updated.pdf", "PRISTE"),
    "procedures-manual.pdf": (BASE + "2024/11/ALUPE-UNIVERSITY-COLLEGE-PROCEDURES-MANUAL.pdf", None),
    "rules-and-regulations.pdf": (BASE + "2026/08/Alupe-University-Rules-and-Regulations-.pdf", None),
    "special-supplementary-exams.pdf": (BASE + "2026/09/SPECIAL-AND-SUPPLEMENTARY-EXAMS.pdf", None),
    "fee-clearance-reminder.pdf": (BASE + "2026/06/FEE-CLEARANCE-REMINDER.pdf", None),
}

out = Path("downloads")
out.mkdir(exist_ok=True)

for name, (url, keyword) in SOURCES.items():
    print("=" * 80)
    print(name)

    path = out / name
    if path.exists():
        print("  using the file already in downloads/")
    else:
        try:
            r = polite_get(url)
        except Exception as e:
            print("  FAILED:", type(e).__name__, e)
            continue
        path.write_bytes(r.content)

    size_kb = path.stat().st_size / 1024
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        text = " ".join(
            " ".join((p.extract_text() or "").split()) for p in reader.pages
        )
    except Exception as e:
        print("  Could not read PDF:", e)
        continue

    print(f"  {size_kb:.0f} KB, {pages} pages, {len(text)} chars of text")
    if len(text) < 100 * max(pages, 1):
        print("  WARNING: very little text, probably a scanned image PDF")
    print("  preview:", text[:300])

    if keyword:
        pos = text.upper().find(keyword)
        if pos != -1:
            print(f"  around '{keyword}':", text[max(pos - 150, 0):pos + 350])
        else:
            print(f"  '{keyword}' not found in the extracted text")