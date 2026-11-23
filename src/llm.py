"""Lớp gọi mô hình AI: hỗ trợ Gemini (qua mạng) và Ollama (chạy trên máy).

- chat(...)        : trả về toàn bộ câu trả lời một lần
- chat_stream(...) : trả về câu trả lời từng đoạn nhỏ (hiện chữ dần trên giao diện)
"""
from typing import Iterator

from src.config import GEMINI_API_KEY, GEMINI_MODEL, OLLAMA_MODEL, PROVIDER

SYSTEM = "Bạn là trợ lý hữu ích, trả lời bằng tiếng Việt."

_client = None


def _clean(history: list) -> list:
    """Chỉ giữ role và content, bỏ các trường phụ (thời gian, ...)."""
    return [{"role": m["role"], "content": m["content"]} for m in history]


# ------------------------------------------------------------------ Gemini
def _gemini_client():
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _gemini_request(history: list, system: str):
    from google.genai import types

    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in _clean(history)
    ]
    config = types.GenerateContentConfig(system_instruction=system)
    return contents, config


def _chat_gemini(history: list, system: str) -> str:
    contents, config = _gemini_request(history, system)
    response = _gemini_client().models.generate_content(
        model=GEMINI_MODEL, contents=contents, config=config
    )
    return response.text or ""


def _stream_gemini(history: list, system: str) -> Iterator[str]:
    contents, config = _gemini_request(history, system)
    stream = _gemini_client().models.generate_content_stream(
        model=GEMINI_MODEL, contents=contents, config=config
    )
    for chunk in stream:
        if chunk.text:
            yield chunk.text


# ------------------------------------------------------------------ Ollama
def _ollama_messages(history: list, system: str) -> list:
    return [{"role": "system", "content": system}] + _clean(history)


def _chat_ollama(history: list, system: str) -> str:
    import ollama

    response = ollama.chat(model=OLLAMA_MODEL, messages=_ollama_messages(history, system))
    return response["message"]["content"]


def _stream_ollama(history: list, system: str) -> Iterator[str]:
    import ollama

    stream = ollama.chat(
        model=OLLAMA_MODEL, messages=_ollama_messages(history, system), stream=True
    )
    for part in stream:
        text = part["message"]["content"]
        if text:
            yield text


# ------------------------------------------------------------- Hàm công khai
def chat(history: list, system: str = SYSTEM) -> str:
    if PROVIDER == "ollama":
        return _chat_ollama(history, system)
    return _chat_gemini(history, system)


def chat_stream(history: list, system: str = SYSTEM) -> Iterator[str]:
    if PROVIDER == "ollama":
        return _stream_ollama(history, system)
    return _stream_gemini(history, system)