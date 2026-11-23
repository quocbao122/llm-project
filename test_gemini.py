import time

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_MODEL

MODELS = []
for m in [GEMINI_MODEL, "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"]:
    if m not in MODELS:
        MODELS.append(m)

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=30_000))

print("Đang thử từng model (mỗi model tối đa 30 giây)...\n")
for model in MODELS:
    start = time.time()
    try:
        r = client.models.generate_content(model=model, contents="Trả lời đúng một từ: Xin chào")
        print(f"[OK]  {model}: {time.time() - start:.1f} giây -> {(r.text or '').strip()[:60]}")
    except Exception as e:
        print(f"[LỖI] {model}: {time.time() - start:.1f} giây -> {type(e).__name__}: {str(e)[:150]}")