from .retriever import search
from .llm import ask

SYSTEM = (
    "You are a friendly voice assistant. "
    "You are given some context from the user's documents. "
    "If the context contains the answer, use it. "
    "If the context is not relevant, ignore it and answer from your own general knowledge. "
    "Keep answers short (1-3 sentences) and plain text, since they will be spoken aloud."
)


def answer(question: str) -> str:
    try:
        context = "\n\n".join(search(question))
    except Exception:
        context = ""
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    return ask(SYSTEM, prompt)