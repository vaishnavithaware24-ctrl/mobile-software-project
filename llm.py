import os

_client = None
_model = None

PREFERRED = [
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
]
SKIP = ("whisper", "guard", "tts", "orpheus", "playai", "compound", "safeguard")


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
    return _client


def _pick_model(client):
    ids = [m.id for m in client.models.list().data]
    for name in PREFERRED:
        if name in ids:
            return name
    usable = [i for i in ids if not any(s in i.lower() for s in SKIP)]
    if not usable:
        raise RuntimeError("No chat model available for this API key")
    return usable[0]


def _chat(client, model, messages):
    resp = client.chat.completions.create(model=model, messages=messages)
    return (resp.choices[0].message.content or "").strip()


def ask(system_prompt, user_prompt):
    global _model
    client = _get_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if _model is None:
        _model = os.getenv("LLM_MODEL") or _pick_model(client)

    try:
        return _chat(client, _model, messages)
    except Exception as e:
        text = str(e).lower()
        missing = (
            "model_not_found" in text
            or "does not exist" in text
            or "decommissioned" in text
            or "do not have access" in text
        )
        if not missing:
            raise
        _model = _pick_model(client)
        return _chat(client, _model, messages)