from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
from logger import log_unanswered
from rag import answer
from ratelimit import RateLimiter

app = FastAPI(title="AU Smart Assistant")

# Your own page is served from the same address, so it needs no CORS.
# Only websites listed in ALLOWED_ORIGINS may call the API from their pages.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

per_minute = RateLimiter(config.RATE_PER_MINUTE, 60)
per_day = RateLimiter(config.RATE_PER_DAY, 86400)
global_per_day = RateLimiter(config.RATE_GLOBAL_PER_DAY, 86400)


class Message(BaseModel):
    # Literal blocks a client from sending role "system" to hijack the bot
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[Message] = []


@app.get("/")
def root():
    ancestors = " ".join(["'self'"] + config.ALLOWED_ORIGINS)
    return FileResponse(
        "static/index.html",
        headers={"Content-Security-Policy": f"frame-ancestors {ancestors}"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    ip = request.client.host
    if not (per_minute.allow(ip) and per_day.allow(ip)):
        raise HTTPException(status_code=429, detail="Too many messages. Please wait a moment.")
    if not global_per_day.allow("all"):
        raise HTTPException(status_code=503, detail="You reached your daily limit. Please try again tomorrow.")

    history = [m.model_dump() for m in req.history[-6:]]
    try:
        result = answer(req.question.strip(), history)
    except Exception as e:
        print(f"Error in /chat: {e}")
        raise HTTPException(
            status_code=503,
            detail="AU Assistant is temporarily unavailable. Please try again after 5 minutes.",
        )

    if not result["answered"]:
        log_unanswered(req.question.strip(), result["search_query"], result["top_score"])

    return {"answer": result["answer"], "sources": result["sources"]}