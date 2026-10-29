"""Retrieves the stored information in chunks
   Run it on it's own (python retrieval.py) and make sure its retriving data before integrating LLM
   Can't work? LLM can't save
   """

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

import config

from termcolor import colored

# Loaded once when the module is imported (FastAPI will reuse these)
_model = SentenceTransformer(config.EMBEDDING_MODEL)
_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)


def retrieve(question, top_k=10):
    """Return the top_k most relevant chunks for a question."""
    vector = _model.encode(question).tolist()
    hits = _client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=vector,
        limit=top_k,
    ).points

    return [
        {
            "text": h.payload["text"],
            "source": h.payload["source"],
            "page": h.payload["page"],
            "score": h.score,
        }
        for h in hits
    ]


if __name__ == "__main__":
    while True:
        q = input(colored("\nQuestion (or 'quit'): ", "blue")).strip()
        if q.lower() == "quit":
            break
        for r in retrieve(q):
            print(f"\n[{r['score']:.3f}] {r['source']} (p.{r['page']})")
            print(r["text"][:300] + "...")