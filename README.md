# Smart Knowledge Assistant

A chatbot that answers questions from your own documents. Python (FastAPI) backend, Qdrant for vector search, Groq-hosted language models, and a plain HTML/CSS/JavaScript chat page.

It answers only from the documents you give it. When it can't find an answer, it says so and logs the question so you can see what content is missing.

## How it works

1. `ingest.py` splits your documents into chunks, embeds them locally, and stores them in Qdrant.
2. For each question, the app rewrites follow-ups into standalone questions, retrieves the most relevant chunks, and asks the language model to answer using only those chunks.
3. If nothing relevant is found, it replies politely and records the question.

## Requirements

- Python 3.10 or newer
- A [Qdrant](https://qdrant.tech) cluster (URL and API key)
- A [Groq](https://console.groq.com) API key

Python libraries:

| Library | Used for |
|---|---|
| `fastapi` | Web API and serving the chat page |
| `uvicorn` | Server that runs the FastAPI app |
| `pydantic` | Request validation (installed with FastAPI) |
| `qdrant-client` | Storing and searching vectors in Qdrant |
| `sentence-transformers` | Local embedding model |
| `torch` | Runs the embedding model (CPU build, installed separately below) |
| `pypdf` | Extracting text from PDFs |
| `groq` | Calling Groq-hosted language models |
| `python-dotenv` | Loading settings from `.env` |
| `requests` | Downloads in the optional helper scripts |
| `beautifulsoup4` | HTML parsing in the optional helper scripts |

Everything else the code imports (`sqlite3`, `re`, `uuid`, `threading` and so on) is part of Python's standard library.

## Installation

```bash
git clone <your-repo-url>
cd <your-repo>

python3 -m venv venv
source venv/bin/activate

# CPU-only PyTorch first, to avoid large GPU downloads
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
QDRANT_URL=https://your-cluster-url:6333
QDRANT_API_KEY=your-qdrant-key
GROQ_API_KEY=your-groq-key

# Optional: websites allowed to call the API from a browser (comma-separated)
# ALLOWED_ORIGINS=https://www.example.com
```

Make sure `.env`, `venv/` and `logs/` are in your `.gitignore`.

## Usage

**1. Add your documents.** Put PDFs in `data/`. They must contain real text. Scanned images produce nothing and need OCR first.

**2. Build the index.**

```bash
python ingest.py
```

Run this again whenever your documents change. Each run rebuilds the collection from scratch.

**3. Start the server.**

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` for the chat page, or `http://127.0.0.1:8000/docs` to try the API. Start Uvicorn from the project root.

**4. Test from the terminal (optional).**

```bash
python retrieval.py   # shows the ranked chunks and scores for a question
python rag.py         # chat in the terminal, shows the rewritten query and top score
```

**5. Review unanswered questions.**

```bash
python show_unanswered.py
```

Repeated entries point to documents you should add or update.

### Structured documents

Table-heavy PDFs often extract badly because values end up next to the wrong rows. For those, save a cleaned and verified plain-text version in `cleaned/`. Each block separated by a blank line becomes one chunk, so a record's details are never split apart. Blocks that start with `HOSTEL:` also feed generated summary chunks. Edit `records_from_cleaned` in `ingest.py` to suit your own data.

## Configuration

Edit `config.py`:

| Setting | Meaning |
|---|---|
| `COLLECTION_NAME` | Qdrant collection name. Use a new one if you change the embedding model. |
| `EMBEDDING_MODEL`, `VECTOR_SIZE` | Embedding model and its output size (384 for the default MiniLM model). They must match. |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Characters per chunk. Keep chunks within the embedding model's input limit (about 1,000 characters for the default model), because text beyond it is not searchable. |
| `TOP_K` | Chunks retrieved per question. Higher helps list-style questions but uses more tokens. |
| `MIN_SCORE` | Similarity cutoff below which a question counts as not covered. Re-tune if you change the embedding model. |
| `GROQ_MODEL`, `REWRITE_MODEL` | Answering model, and a smaller model for rewriting and small talk. |
| `CONTACT`, `NO_INFO_MESSAGE` | Contact details and the standard reply when there is no answer. |
| `RATE_PER_MINUTE`, `RATE_PER_DAY`, `RATE_GLOBAL_PER_DAY` | Per-IP and total daily message limits. |

Model names change over time. Run `python list_models.py` to see which models your Groq account can use.

## API

`POST /chat`

```json
{
  "question": "What are the opening hours?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}
```

- `question`: 1 to 500 characters.
- `history`: optional. Only the last 6 messages are used. Each `content` is at most 2,000 characters, and `role` is `user` or `assistant`.

Response:

```json
{
  "answer": "...",
  "sources": [{"source": "file.pdf", "page": 2}]
}
```

`sources` lists the chunks that were retrieved, not necessarily the ones the answer relied on.

Errors: `422` invalid input, `429` rate limit reached, `503` model provider failure or daily limit reached.

`GET /health` returns `{"status": "ok"}`.

The server keeps no conversation state. The chat page stores the conversation in the browser and sends recent history with every request.

## Project structure

```
main.py              FastAPI app: /chat, /health, serves the chat page
rag.py               Pipeline: small talk, rewrite, retrieve, answer, fallback
retrieval.py         Embeds a question and searches Qdrant
ingest.py            Builds the index from data/ and cleaned/
config.py            Settings
ratelimit.py         Rate limiter
logger.py            Logs unanswered questions to logs/unanswered.db
show_unanswered.py   Prints recent unanswered questions
list_models.py       Lists the models available to your Groq key
static/              index.html, style.css, app.js
data/                Source PDFs
cleaned/             Verified plain-text versions of table-heavy sources
```

The other scripts (`fetch_pdfs.py`, `explore_site.py`, `probe_pages.py`, `clean_accommodation.py`, `check_cleaned.py`, `debug_hostels.py`, `polite.py`) are optional helpers for downloading and cleaning source documents.

## Deployment

- Start command behind a proxy:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips "*"
  ```
  Without the proxy flags, every visitor appears to share the proxy's IP address and the rate limiter blocks everyone together. Use `"*"` only when a trusted proxy is in front.
- Set `QDRANT_URL`, `QDRANT_API_KEY`, `GROQ_API_KEY` and `ALLOWED_ORIGINS` as environment variables on the host.
- `logs/unanswered.db` is lost on redeploy unless it is on persistent storage.
- The embedding model (about 90 MB) downloads on first start and loads into memory alongside PyTorch, so check your host's RAM.
- Run `python ingest.py` from your own machine against the hosted Qdrant. The server doesn't need to ingest.
- Rate-limit counters live in memory, so they reset on restart and are not shared between workers.

## Troubleshooting

| Problem | Fix |
|---|---|
| Groq error `model_not_found` (404) | Run `python list_models.py` and update `GROQ_MODEL` and `REWRITE_MODEL`. |
| Groq error `413` or `429` | Lower `TOP_K`, or switch to a smaller model. |
| Qdrant vector dimension error | `VECTOR_SIZE` must match the embedding model. Use a new `COLLECTION_NAME` and re-run `ingest.py`. |
| Chat page unstyled or outdated after an edit | Hard-refresh the browser (Ctrl+Shift+R). |
| `404` at `/` | Start Uvicorn from the project root so `static/` is found. |
| Everyone gets `429` after deployment | Add the proxy flags to the start command (see Deployment). |
