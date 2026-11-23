import time

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=60_000))

# 1. Hỏi Google xem key của bạn dùng được những model nào
names = []
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        names.append(m.name.replace("models/", ""))

print(f"Key của bạn dùng được {len(names)} model. Các model Flash:")
skip = ("image", "tts", "live", "audio", "native", "computer", "robotics", "embedding")
flash = [n for n in names if "flash" in n and not any(s in n for s in skip)]
for n in flash:
    print("  -", n)

# 2. Thử tối đa 4 model, ưu tiên bản lite (nhẹ, nhanh)
flash.sort(key=lambda n: (0 if "lite" in n else 1, n))
print("\nĐang thử tối đa 4 model (mỗi model tối đa 60 giây)...\n")
for model in flash[:4]:
    start = time.time()
    try:
        r = client.models.generate_content(model=model, contents="Trả lời đúng một từ: Xin chào")
        print(f"[OK]  {model}: {time.time() - start:.1f} giây -> {(r.text or '').strip()[:60]}")
    except Exception as e:
        print(f"[LỖI] {model}: {time.time() - start:.1f} giây -> {type(e).__name__}: {str(e)[:120]}")