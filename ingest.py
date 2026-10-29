
"""Ingest the feed data(files) to a retrivable form
   NOTE; Image-like data(including PDF images) cant be return beside been scanned(pypdf returns only text data)
   """
import re
import uuid
from pathlib import Path

from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

import config


# ---------- PDFs ----------

def load_pdf(path):
    reader = PdfReader(path)
    full_text = ""
    page_starts = []  # (character offset where the page begins, page number)
    for page_num, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        if text:
            page_starts.append((len(full_text), page_num))
            full_text += text + " "
    return full_text, page_starts


def page_for_offset(page_starts, offset):
    page = page_starts[0][1]
    for start, num in page_starts:
        if start <= offset:
            page = num
        else:
            break
    return page


def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append((start, text[start:end]))
        if end >= len(text):
            break
        start += size - overlap
    return chunks


def records_from_pdf(pdf):
    full_text, page_starts = load_pdf(pdf)
    if not full_text.strip():
        return []
    return [
        {"text": chunk, "source": pdf.name,
         "page": page_for_offset(page_starts, start), "idx": idx}
        for idx, (start, chunk) in enumerate(
            chunk_text(full_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        )
    ]


# ---------- cleaned text files (one block = one chunk) ----------

def records_from_cleaned(path):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")) if b.strip()]
    records = []
    summary_lines = {"Female": [], "Male": []}

    for idx, block in enumerate(blocks):
        if block.startswith("HOSTEL:"):
            text = "Alupe University student hostel, 2026/2027 academic year.\n" + block
            name = block.splitlines()[0].replace("HOSTEL:", "").strip()
            gender = re.search(r"^Gender:\s*(\w+)", block, re.M)
            options = [o.strip() for o in re.findall(r"^Option \d+:\s*(.*)$", block, re.M)]
            if gender and options and gender.group(1) in summary_lines:
                summary_lines[gender.group(1)].append(f"- {name}: " + " | ".join(options))
        else:
            text = block
        records.append({"text": text, "source": path.name, "page": 1, "idx": idx})

    # Built by code from the verified blocks, so it can never disagree with them
    for n, (gender, lines) in enumerate(summary_lines.items()):
        if lines:
            text = (f"SUMMARY: ALL {gender.upper()} HOSTELS AND THEIR RENT PER SEMESTER, "
                    f"2026/2027 academic year ({len(lines)} hostels)\n" + "\n".join(lines))
            records.append({"text": text, "source": path.name, "page": 1, "idx": 1000 + n})
    return records


# ---------- storing ----------

def store(model, client, source_name, records):
    vectors = model.encode([r["text"] for r in records], show_progress_bar=True)
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{r['source']}-{r['idx']}")),
            vector=vec.tolist(),
            payload=r,
        )
        for vec, r in zip(vectors, records)
    ]
    for i in range(0, len(points), 100):
        client.upsert(collection_name=config.COLLECTION_NAME, points=points[i:i + 100])
    print(f"  Stored {len(points)} chunks from {source_name}")


def main():
    pdf_files = sorted(Path("data").glob("*.pdf"))
    cleaned_files = sorted(Path("cleaned").glob("*.txt"))
    if not pdf_files and not cleaned_files:
        print("Nothing to ingest.")
        return

    print("Loading embedding model...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

    # Full rebuild every run: avoids orphan chunks when sources change
    if client.collection_exists(config.COLLECTION_NAME):
        client.delete_collection(config.COLLECTION_NAME)
    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config=VectorParams(size=config.VECTOR_SIZE, distance=Distance.COSINE),
    )

    for pdf in pdf_files:
        print(f"\nProcessing {pdf.name}...")
        records = records_from_pdf(pdf)
        if not records:
            print("  No extractable text (scanned PDF?). Skipping.")
            continue
        store(model, client, pdf.name, records)

    for txt in cleaned_files:
        print(f"\nProcessing {txt.name}...")
        store(model, client, txt.name, records_from_cleaned(txt))


if __name__ == "__main__":
    main()