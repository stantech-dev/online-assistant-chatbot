"""Configurations of main API keys && Retrieval chunks"""

import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL") # os.getenv imports the credentials from .env file
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

#-------------   EMBEDDING MODEL    ----------

COLLECTION_NAME = "au_assistant_v2"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2" # runs locally 
VECTOR_SIZE = 384  # must match the embedding model's output

CHUNK_SIZE = 1000     # characters per chunk
CHUNK_OVERLAP = 200  # characters shared between neighbouring chunks

#--------    LLM MODEL    -------

"""Human like responses"""
GROQ_MODEL = "openai/gpt-oss-120b"
REWRITE_MODEL = "openai/gpt-oss-20b"
TOP_K = 15
MIN_SCORE = 0.25 

CONTACT = "enquiries@au.ac.ke or 0741214185 / 0736044469" # institute contact info
#Unavailable information
NO_INFO_MESSAGE = (
    "I don't have that information. Please contact the university at " + CONTACT + "."
)

RATE_PER_MINUTE = 10
RATE_PER_DAY = 150
RATE_GLOBAL_PER_DAY = 1500  # Match with Groq limits

# Websites allowed to call the API from a browser.
# Example in .env: ALLOWED_ORIGINS=https://www.au.ac.ke,https://au.ac.ke
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
]