"""Debugs Incomplete retrieved hostel list"""
from retrieval import retrieve
from pypdf import PdfReader

query = "What hostels are available at Alupe University?"
for r in retrieve(query, top_k=20):
    i = r["text"].find("Gift Host")
    if i != -1:
        print(f"--- {r['source']} p.{r['page']} ---")
        print(r["text"][i:i + 350])
        print()

#-------------------- MALE HOSTELS--------------
text = " ".join(
    " ".join((p.extract_text() or "").split())
    for p in PdfReader("data/AU_Hostels_Clean.pdf").pages
)
for name in ["Hames", "Image", "Recabites"]:
    i = text.find(name)
    print(name, "->", text[max(i - 20, 0):i + 250] if i != -1 else "NOT FOUND", "\n")