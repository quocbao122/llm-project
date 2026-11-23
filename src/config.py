
import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(key, default=None):
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


PROVIDER = os.getenv("LLM_PROVIDER") or get_secret("LLM_PROVIDER", "gemini")

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or get_secret("GEMINI_API_KEY")
)

GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL")
    or get_secret("GEMINI_MODEL", "gemini-3.1-flash-lite")
)

OLLAMA_MODEL = (
    os.getenv("OLLAMA_MODEL")
    or get_secret("OLLAMA_MODEL", "qwen2.5:3b")
)

if PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise RuntimeError("Thiếu GEMINI_API_KEY trong Streamlit Secrets hoặc .env")
