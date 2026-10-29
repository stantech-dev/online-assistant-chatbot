"""Checks the cleaned data match the original raw data"""
import re
from collections import Counter

from pypdf import PdfReader


RAW = "downloads/accommodation-2026-27.pdf"  #CHANGE to your file/directory name
CLEANED = "cleaned/accommodation-2026-27.txt"

PRICE = re.compile(r"(?<!\d)\d{1,3},\d{3}(?!\d)")  # formatting

#----Reads and packs both data-------#
raw = " ".join(p.extract_text() or "" for p in PdfReader(RAW).pages)
cleaned = open(CLEANED, encoding="utf-8").read()

#----Row counts------#
raw_counts = Counter(PRICE.findall(raw))
clean_counts = Counter(PRICE.findall(cleaned))

print("Price figures: how often each appears in the raw vs the cleaned data")
for price in sorted(set(raw_counts) | set(clean_counts)):
    r, c = raw_counts[price], clean_counts[price]
    flag = "" if r == c else "   <-- MISMATCH"
    print(f" ksh: {price:>7}: pdf {r:2d}   cleaned {c:2d}{flag}")

blocks = [b for b in re.split(r"\n\s*\n", cleaned) if b.strip().startswith("HOSTEL:")]
print(f"\n{len(blocks)} hostel blocks (I count 22 in the PDF)")

for b in blocks:
    name = b.splitlines()[0]
    declared = re.search(r"Price options:\s*(\d+)", b)
    actual = len(re.findall(r"^Option \d+:", b, re.M))
    problems = []
    if not declared:
        problems.append("no 'Price options' line")
    elif int(declared.group(1)) != actual:
        problems.append(f"says {declared.group(1)} options but has {actual}")
    if "UNCLEAR" in b:
        problems.append("contains UNCLEAR")
    if problems:
        print(f"  CHECK: {name}: {'; '.join(problems)}")

names = [b.splitlines()[0] for b in blocks]
for n in sorted({n for n in names if names.count(n) > 1}):
    print(f"  DUPLICATE BLOCK: {n}")
