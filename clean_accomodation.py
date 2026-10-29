from pathlib import Path

from groq import Groq
from pypdf import PdfReader

import config

PDF_PATH = "downloads/accommodation-2026-27.pdf"
OUT_PATH = Path("cleaned/accommodation-2026-27.txt")

# False = bank accounts and paybill numbers are left out of the cleaned text.
# A mis-paired payment number sends a student's money to the wrong person.
INCLUDE_PAYMENT_DETAILS = False

payment_rule = (
    "Payment: <bank, paybill, till and account numbers>"
    if INCLUDE_PAYMENT_DETAILS
    else "Do NOT include bank names, paybill, till or account numbers anywhere."
)

PROMPT = f"""You convert text extracted from a PDF table into clean plain text.

The source is Alupe University's list of identified student hostels for 2026/2027. The extracted text is jumbled: table cells are out of order, and prices, room sizes and contacts from one hostel can be interleaved with another's.

Output one block per hostel, separated by a blank line, in this format:

HOSTEL: <name>
Gender: Female or Male
Price options: <how many price options this hostel has>
Option 1: Ksh <price> per student, <n> persons per room, <self-contained or not self-contained>; Health Science students pay Ksh <price>
Option 2: <same format, only if the hostel has a second option>
Amenities: <list>
Contacts: <role, name and phone number for each person listed>
{payment_rule}

Rules:
- Many hostels have TWO price options (for example 2 persons per room and 4 persons per room). The second option's price, room size and Health Science price often appear AFTER the contact details, or after a page break. They still belong to the hostel whose name came last before them.
- Never create a second block for a second option. One hostel is always exactly one block.
- Hostels with similar names (for example GIFT LOLU and GIFT ANNEX) are separate hostels. Do not merge them.
- Copy every number exactly as it appears. Never guess, round or correct a number.
- If you cannot tell which hostel a price belongs to, write "UNCLEAR:" followed by the raw text instead of guessing.
- After the last hostel, add a block "GENERAL NOTES" with the numbered notes from the end of the document, copied faithfully.
- Output only the cleaned text, nothing else."""

reader = PdfReader(PDF_PATH)
raw_text = "\n\n--- page break ---\n\n".join(p.extract_text() or "" for p in reader.pages)

client = Groq(api_key=config.GROQ_API_KEY)
response = client.chat.completions.create(
    model=config.GROQ_MODEL,
    messages=[
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": raw_text},
    ],
    temperature=0,
    reasoning_effort="medium",
    max_completion_tokens=8000,
)

cleaned = response.choices[0].message.content.strip()
OUT_PATH.parent.mkdir(exist_ok=True)
OUT_PATH.write_text(cleaned, encoding="utf-8")
print(cleaned)
print(f"\nSaved to {OUT_PATH}")