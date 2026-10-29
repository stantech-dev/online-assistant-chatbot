"""Retrieval-Augmented Generation Bot Building"""
import re

from groq import Groq

import config
from retrieval import retrieve

_groq = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = f"""You are the AU Smart Assistant, the official virtual AI assistant of Alupe University in Busia County, Kenya.

Rules:
- Answer ONLY from the CONTEXT below. Do not use outside knowledge about the university.
- If the CONTEXT does not contain the answer, begin your reply with the exact token [NO_ANSWER], then say you don't have the full details on that and suggest contacting {config.CONTACT}.
- If the question is unclear about what it refers to, ask the user to clarify instead of guessing.
- Be clear, friendly and concise. Use short bullet lists when the answer has several items (hostels, fees, etc). Do not use markdown tables.
- Never invent fees, dates, phone numbers or names. Copy figures exactly as they appear in the context.
- Never mention "the context", "the excerpt", "the document" or "the provided text" to the user.
- When a hostel or programme has several price options, state every option with its price and room size. Never give only the first one.
- When giving hostel rent, also give the Health Science price if one is listed, and say it applies to students taking Health Science courses.
"""

REWRITE_PROMPT = """You rewrite a user's latest message into a standalone search question.

Rules:
- Only resolve references such as "it", "that", "there", "they", or a missing subject, using the conversation.
- Do NOT add details the user did not imply. If the message introduces a new topic, keep it on that topic.
- If the message is already standalone, return it unchanged.
- If you cannot tell what a reference points to, return the message unchanged.
- Output ONLY the rewritten question.

Example:
Conversation: the user asked about the Medical Psychology course.
Latest message: "and the library hours?"
Output: What are the library hours at Alupe University?
"""

CHAT_FALLBACK_PROMPT = """You are the AU Smart Assistant for Alupe University. In this step you have NO knowledge of university facts.

If the user's message is casual conversation (how are you, who are you, what can you do, thanks, ok, a compliment,yo,niaje,what's up,uko aje), reply in one or two friendly sentences and invite them to ask about Alupe University programmes, fees, hostels, procedures or staff.

For anything else, including any question that asks for facts, reply with exactly: NO_INFO"""

GREETING_REPLY = (
    "Hello! I'm the AU Smart Assistant. How can I help you today?\n"
    "Programmes? Fees? Hostels? Procedures? Staff and general questions about Alupe University? What would you like to know?"
)

SMALL_TALK = [
    (re.compile(r"^\s*(hi|hello|hey|hallo|habari|jambo|yo|niaje|good (morning|afternoon|evening))"
                r"( there| assistant)?[\s!.,?]*$", re.I), GREETING_REPLY),
    (re.compile(r"^\s*(thanks|thank you|asante|thx|sawa)( a lot| so much)?[\s!.,]*$", re.I),
     "You're welcome! Let me know if you need anything else about Alupe University."),
    (re.compile(r"^\s*(bye|goodbye|see you|kwaheri|fiti|fity)[\s!.,]*$", re.I),
     "Goodbye! Feel free to come back anytime you have a question about Alupe University."),
]


def small_talk_reply(question):
    for pattern, reply in SMALL_TALK:
        if pattern.match(question):
            return reply
    return None


def rewrite_question(question, history):
    """Turn a follow-up into a standalone question so retrieval can find the right chunks."""
    if not history:
        return question

    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    response = _groq.chat.completions.create(
        model=config.REWRITE_MODEL,
        messages=[
            {"role": "system", "content": REWRITE_PROMPT},
            {"role": "user", "content": f"Conversation:\n{convo}\n\nLatest message: {question}"},
        ],
        temperature=0,
        reasoning_effort="low",
    )
    return response.choices[0].message.content.strip()


def fallback_reply(question):
    """Called only when retrieval found nothing relevant."""
    try:
        response = _groq.chat.completions.create(
            model=config.REWRITE_MODEL,
            messages=[
                {"role": "system", "content": CHAT_FALLBACK_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.3,
            reasoning_effort="low",
        )
        text = response.choices[0].message.content.strip()
    except Exception:
        return config.NO_INFO_MESSAGE

    if "NO_INFO" in text:
        return config.NO_INFO_MESSAGE
    return text


def build_context(chunks):
    return "\n\n---\n\n".join(
        f"[Source: {c['source']}, page {c['page']}]\n{c['text']}" for c in chunks
    )


def answer(question, history=None):
    reply = small_talk_reply(question)
    if reply:
        return {"answer": reply, "answered": True, "sources": [],
                "top_score": 0.0, "search_query": question}

    search_query = rewrite_question(question, history)

    found = retrieve(search_query, config.TOP_K)
    top_score = found[0]["score"] if found else 0.0
    chunks = [c for c in found if c["score"] >= config.MIN_SCORE]

    if not chunks:
        reply = fallback_reply(question)
        return {"answer": reply, "answered": reply != config.NO_INFO_MESSAGE,
                "sources": [], "top_score": top_score, "search_query": search_query}

    # The answering model never sees the conversation, only the standalone question
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\nCONTEXT:\n" + build_context(chunks)},
        {"role": "user", "content": search_query},
    ]
    response = _groq.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        reasoning_effort="low",
    )

    text = response.choices[0].message.content.strip()
    answered = "[NO_ANSWER]" not in text
    text = text.replace("[NO_ANSWER]", "").strip()

    sources = sorted({(c["source"], c["page"]) for c in chunks})
    return {
        "answer": text,
        "answered": answered,
        "sources": [{"source": s, "page": p} for s, p in sources],
        "top_score": top_score,
        "search_query": search_query,
    }


if __name__ == "__main__":
    history = []
    while True:
        q = input("\nQuestion (or 'quit'): ").strip()
        if q.lower() == "quit":
            break
        result = answer(q, history)
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": result["answer"]})

        print(f"\n{result['answer']}")
        print(f"\n(searched for: {result['search_query']})")
        print(f"(top score: {result['top_score']:.3f}, answered: {result['answered']})")