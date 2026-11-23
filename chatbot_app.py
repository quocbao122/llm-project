"""
My AI Assistant - ứng dụng chatbot với Streamlit.

Chạy:  streamlit run chatbot_app.py

Tính năng: trả lời hiện dần (streaming), nhiều vai trò AI, lịch sử hội thoại lưu file,
tìm kiếm, đổi tên, xóa, tải về .md, tạo lại câu trả lời, thông báo lỗi dễ hiểu.
"""
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# Tìm thư mục gốc của dự án (thư mục chứa src/), dù file này nằm ở đâu
ROOT = Path(__file__).resolve().parent
while not (ROOT / "src").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.config import GEMINI_MODEL, OLLAMA_MODEL, PROVIDER  # noqa: E402
from src.llm import chat_stream  # noqa: E402

st.set_page_config(page_title="My AI Assistant", page_icon="🤖", layout="wide")

DATA_DIR = ROOT / "data"
HISTORY_FILE = DATA_DIR / "conversations.json"
MODEL_NAME = OLLAMA_MODEL if PROVIDER == "ollama" else GEMINI_MODEL
MAX_CONTEXT = 20  # chỉ gửi 20 tin nhắn gần nhất cho AI để tiết kiệm lượt dùng
NEW_TITLE = "Cuộc trò chuyện mới"

# ---------------------------------------------------------------- Vai trò AI
PERSONAS = {
    "Trợ lý đa năng": {
        "icon": "✨",
        "prompt": (
            "Bạn là trợ lý AI hữu ích, thân thiện, trả lời bằng tiếng Việt, rõ ràng và đúng trọng tâm. "
            "Khi không chắc chắn, hãy nói thẳng thay vì đoán."
        ),
        "starters": [
            "Giải thích API là gì cho người mới học",
            "Lập kế hoạch học lập trình trong 30 ngày",
            "Viết giúp mình email xin nghỉ phép lịch sự",
            "Gợi ý cách quản lý thời gian hiệu quả",
        ],
    },
    "Mentor lập trình": {
        "icon": "💻",
        "prompt": (
            "Bạn là mentor lập trình giàu kinh nghiệm, hướng dẫn người mới bằng tiếng Việt. "
            "Giải thích dễ hiểu, luôn kèm ví dụ code ngắn và giải thích từng phần."
        ),
        "starters": [
            "Khác nhau giữa list và dictionary trong Python?",
            "REST API là gì? Cho ví dụ với FastAPI",
            "Git branch và merge hoạt động thế nào?",
            "Cách đọc và hiểu một lỗi Traceback trong Python",
        ],
    },
    "Mentor kiểm thử (QA)": {
        "icon": "🧪",
        "prompt": (
            "Bạn là chuyên gia QA/QC giàu kinh nghiệm, hướng dẫn người mới học kiểm thử phần mềm "
            "bằng tiếng Việt: viết test case, kỹ thuật thiết kế test, báo cáo bug, quy trình kiểm thử. "
            "Luôn có ví dụ cụ thể."
        ),
        "starters": [
            "Viết test case cho chức năng đăng nhập",
            "Phân biệt QA và QC, Tester và Developer",
            "Phân vùng tương đương và giá trị biên là gì?",
            "Cách viết bug report chuẩn",
        ],
    },
    "Cố vấn CV và phỏng vấn": {
        "icon": "📄",
        "prompt": (
            "Bạn là cố vấn nghề nghiệp cho sinh viên mới ra trường ngành CNTT, trả lời bằng tiếng Việt. "
            "Góp ý cụ thể, trung thực, không bịa thêm kinh nghiệm cho người dùng. "
            "Khi luyện phỏng vấn, hãy hỏi từng câu một và nhận xét câu trả lời."
        ),
        "starters": [
            "Góp ý cách viết mục dự án trong CV fresher",
            "Các câu hỏi phỏng vấn Tester thường gặp",
            "Trả lời thế nào khi được bảo giới thiệu bản thân?",
            "Viết email ứng tuyển thực tập",
        ],
    },
    "Gia sư tiếng Anh": {
        "icon": "🇬🇧",
        "prompt": (
            "Bạn là gia sư tiếng Anh thân thiện cho người Việt. Giải thích bằng tiếng Việt, "
            "ví dụ bằng tiếng Anh. Khi người học viết tiếng Anh, sửa lỗi nhẹ nhàng và giải thích lý do."
        ),
        "starters": [
            "Phân biệt thì hiện tại hoàn thành và quá khứ đơn",
            "Cho mình 5 câu giao tiếp khi đi phỏng vấn",
            "Sửa lỗi giúp mình: I am work here since 2020",
            "Luyện hội thoại tiếng Anh về chủ đề công việc",
        ],
    },
}

CSS = """
<style>
.block-container { max-width: 880px; padding-top: 1.8rem; padding-bottom: 5rem; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] .stButton button { justify-content: flex-start; text-align: left; }

.hero h1 {
  margin: 0; padding: 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em;
  background: linear-gradient(90deg, #5EEAD4, #60A5FA);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 4px 0 0 0; color: #8B98A5; }

[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px; padding: 14px 18px;
}
.stButton button, [data-testid="stDownloadButton"] button { border-radius: 12px; }

.empty h2 { margin: 2.2rem 0 .3rem; font-size: 1.5rem; font-weight: 700; }
.empty p { color: #8B98A5; margin-bottom: 1.2rem; }
[class*="st-key-starter"] button {
  min-height: 76px; padding: 12px 16px; border-radius: 14px;
  justify-content: flex-start; text-align: left;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------- Lưu / đọc lịch sử
def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_history() -> None:
    """Ghi file an toàn (ghi file tạm rồi đổi tên) và bỏ qua cuộc trò chuyện rỗng."""
    DATA_DIR.mkdir(exist_ok=True)
    saved = [c for c in st.session_state.chats if c["messages"]]
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


if "chats" not in st.session_state:
    st.session_state.chats = load_history()
if "active_chat" not in st.session_state:
    st.session_state.active_chat = None


# ------------------------------------------------------------- Thao tác chat
def new_chat() -> None:
    chats = st.session_state.chats
    if chats and not chats[0]["messages"]:  # đã có sẵn một cuộc trò chuyện trống thì dùng lại
        st.session_state.active_chat = chats[0]["id"]
        return
    item = {
        "id": str(uuid.uuid4()),
        "title": NEW_TITLE,
        "created": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }
    chats.insert(0, item)
    st.session_state.active_chat = item["id"]


def get_chat() -> dict:
    for item in st.session_state.chats:
        if item["id"] == st.session_state.active_chat:
            return item
    new_chat()
    return get_chat()


def select_chat(chat_id: str) -> None:
    st.session_state.active_chat = chat_id


def delete_chat(chat_id: str) -> None:
    st.session_state.chats = [c for c in st.session_state.chats if c["id"] != chat_id]
    st.session_state.active_chat = None
    save_history()


def clear_all() -> None:
    st.session_state.chats = []
    st.session_state.active_chat = None
    save_history()


def set_pending(text: str) -> None:
    st.session_state.pending_prompt = text


def request_regen() -> None:
    """Tạo lại câu trả lời: bỏ câu trả lời cuối (nếu có) rồi yêu cầu AI trả lời lại."""
    conv = get_chat()
    if conv["messages"] and conv["messages"][-1]["role"] == "assistant":
        conv["messages"].pop()
        save_history()
    st.session_state.regen = True


def to_markdown(conv: dict) -> str:
    lines = [f"# {conv['title']}", ""]
    for m in conv["messages"]:
        who = "Bạn" if m["role"] == "user" else "AI"
        lines += [f"**{who}:**", "", m["content"], ""]
    return "\n".join(lines)


def friendly_error(e: Exception) -> str:
    text = str(e)
    low = text.lower()
    code = getattr(e, "code", None)
    if code == 429 or "quota" in low or "resource_exhausted" in low:
        return "Đã chạm giới hạn lượt gọi của gói miễn phí. Hãy đợi một lúc rồi bấm Thử lại."
    if code in (401, 403) or "api key" in low or "api_key" in low:
        return "API key không hợp lệ hoặc đã hết hạn. Hãy kiểm tra lại file .env."
    if any(w in low for w in ("connect", "timed out", "timeout", "network", "refused")):
        if PROVIDER == "ollama":
            return "Không kết nối được Ollama. Hãy mở ứng dụng Ollama rồi bấm Thử lại."
        return "Không kết nối được tới máy chủ AI. Hãy kiểm tra mạng rồi bấm Thử lại."
    return text[:300] or "Lỗi không xác định."


# ---------------------------------------------------------------- Thanh bên
with st.sidebar:
    st.markdown("### 🤖 My AI")
    if st.button("＋ Cuộc trò chuyện mới", type="primary", use_container_width=True):
        new_chat()
        st.rerun()

    keyword = st.text_input("Tìm kiếm", placeholder="🔍 Tìm trong lịch sử", label_visibility="collapsed")

    st.caption("Lịch sử")
    kw = keyword.strip().lower()
    visible = []
    for item in st.session_state.chats:
        if not item["messages"] and item["id"] != st.session_state.active_chat:
            continue
        if kw and kw not in item["title"].lower() and not any(kw in m["content"].lower() for m in item["messages"]):
            continue
        visible.append(item)

    if not visible:
        st.caption("Không có cuộc trò chuyện nào." if not kw else "Không tìm thấy kết quả phù hợp.")
    for item in visible:
        is_active = item["id"] == st.session_state.active_chat
        label = ("● " if is_active else "💬 ") + item["title"]
        st.button(
            label[:34],
            key=f"chat_{item['id']}",
            use_container_width=True,
            on_click=select_chat,
            args=(item["id"],),
        )

    st.divider()
    persona_name = st.selectbox("Vai trò của AI", list(PERSONAS), key="persona")
    st.caption(f"Nhà cung cấp: {PROVIDER.upper()}")
    st.caption(f"Model: {MODEL_NAME}")

    with st.popover("🗑 Xóa toàn bộ lịch sử", use_container_width=True):
        st.warning("Thao tác này không thể hoàn tác.")
        st.button("Xác nhận xóa tất cả", type="primary", on_click=clear_all)

persona = PERSONAS[persona_name]
conv = get_chat()

# ------------------------------------------------------------ Đầu trang chính
head_left, head_right = st.columns([3, 1], vertical_alignment="center")
with head_left:
    st.markdown(
        f'<div class="hero"><h1>My AI Assistant</h1>'
        f'<p>{persona["icon"]} {persona_name}</p></div>',
        unsafe_allow_html=True,
    )
with head_right:
    if conv["messages"]:
        with st.popover("⚙️ Tùy chọn", use_container_width=True):
            new_title = st.text_input("Tên cuộc trò chuyện", value=conv["title"], key=f"rename_{conv['id']}")
            if st.button("Lưu tên", key=f"save_title_{conv['id']}", use_container_width=True):
                conv["title"] = new_title.strip()[:60] or conv["title"]
                save_history()
                st.rerun()
            st.download_button(
                "⬇️ Tải về (.md)",
                data=to_markdown(conv),
                file_name=f"chat-{conv['id'][:8]}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.button(
                "🗑 Xóa cuộc trò chuyện này",
                key=f"del_{conv['id']}",
                use_container_width=True,
                on_click=delete_chat,
                args=(conv["id"],),
            )

# ------------------------------------------------------ Nhận câu hỏi từ người dùng
typed = st.chat_input("Nhập tin nhắn của bạn...", max_chars=4000)
prompt = typed or st.session_state.pop("pending_prompt", None)
regen = st.session_state.pop("regen", False)

if prompt:
    conv["messages"].append(
        {"role": "user", "content": prompt, "time": datetime.now().isoformat(timespec="seconds")}
    )
    if conv["title"] == NEW_TITLE:
        short = " ".join(prompt.split())
        conv["title"] = short[:40] + ("…" if len(short) > 40 else "")
    save_history()

will_generate = bool(prompt) or regen

# ------------------------------------------------------------ Hiển thị hội thoại
if not conv["messages"]:
    st.markdown(
        '<div class="empty"><h2>Bạn muốn hỏi gì hôm nay?</h2>'
        "<p>Chọn một gợi ý bên dưới hoặc tự nhập câu hỏi.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, text in enumerate(persona["starters"]):
        cols[i % 2].button(
            text,
            key=f"starter_{i}",
            use_container_width=True,
            on_click=set_pending,
            args=(text,),
        )
else:
    for m in conv["messages"]:
        with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🤖"):
            st.markdown(m["content"])
            if m["role"] == "assistant" and m.get("ms"):
                st.caption(f"⏱ {m['ms'] / 1000:.1f} giây")

    if not will_generate:
        last = conv["messages"][-1]
        if last["role"] == "assistant":
            st.button("🔄 Tạo lại câu trả lời", key="regen_btn", on_click=request_regen)
        else:
            st.warning("Câu hỏi này chưa có câu trả lời.")
            st.button("🔁 Thử lại", key="retry_btn", on_click=request_regen)

# ------------------------------------------------------------------ Gọi AI
if will_generate and conv["messages"] and conv["messages"][-1]["role"] == "user":
    history = conv["messages"][-MAX_CONTEXT:]
    while history and history[0]["role"] != "user":  # AI cần bắt đầu bằng lượt của người dùng
        history = history[1:]

    started = time.time()
    with st.chat_message("assistant", avatar="🤖"):
        try:
            answer = st.write_stream(chat_stream(history, system=persona["prompt"]))
            if not answer or not answer.strip():
                raise RuntimeError("AI không trả về nội dung. Hãy thử hỏi lại.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Chưa trả lời được: {friendly_error(e)}")
            st.button("🔁 Thử lại", key="retry_after_error", on_click=request_regen)
            st.stop()

    conv["messages"].append(
        {
            "role": "assistant",
            "content": answer,
            "ms": int((time.time() - started) * 1000),
            "time": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_history()
    st.rerun()